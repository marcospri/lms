import { TinyEmitter } from 'tiny-emitter';

import { Server, call as rpcCall } from '../../postmessage_json_rpc';
import type { ClientConfig } from '../config';
import { apiCall } from '../utils/api';
import { JWT } from '../utils/jwt';

export type User = {
  displayName: string;
  userid: string;
};

export type AnnotationEventType = 'create' | 'update' | 'flag' | 'delete';

export type AnnotationEventData = {
  date: string;
  annotation: {
    id: string;
    isShared: boolean;
  };
};

/**
 * Content provider logo details.
 */
export type ContentInfoLogo = {
  logo: string;
  title: string;
  link: string;
};

/**
 * Metadata for the current document, for display in the content info banner.
 */
export type ContentInfoItem = {
  /** Title of the current article, chapter etc. */
  title: string;
  subtitle?: string;
};

/**
 * Links related to the current document, for display in the content info banner.
 */
export type ContentInfoLinks = {
  /** Previous item in the book, journal etc. */
  previousItem?: string;
  /** Next item in the book, journal etc. */
  nextItem?: string;
  currentItem: string;
};

/**
 * Configuration for content information banner in client.
 *
 * This and other `ContentInfo*` types are copied from the hypothesis/client repo.
 */
export type ContentInfoConfig = {
  /** Logo of the content provider. */
  logo: ContentInfoLogo;
  item: ContentInfoItem;
  container: ContentInfoItem;
  links: ContentInfoLinks;
};

export type ClientRPCOptions = {
  /** Origins that are allowed to request client configuration. */
  allowedOrigins: string[];

  /**
   * Auth token used in LMS backend API calls to refresh the grant token
   * in the `clientConfig` if it has expired
   */
  authToken: string;

  /**
   * Configuration for the Hypothesis client. Whatever is provided here is
   * passed directly to the client via `window.postMessage` when it requests
   * configuration. It should be a subset of the config options specified at
   * https://h.readthedocs.io/projects/client/en/latest/publishers/config/.
   */
  clientConfig: ClientConfig;
};

/**
 * Service for communicating with the Hypothesis client.
 *
 * This service handles:
 *
 *  - Waiting for the Hypothesis client to request its configuration and then
 *    returning the configuration data generated by the LMS backend to the
 *    client.
 *  - Updating the Hypothesis client configuration in response to input
 *    in the LMS frontend, such as changing the focused user in grading mode.
 */
export class ClientRPC extends TinyEmitter {
  private _resolveGroups: (groups: string[]) => void;
  private _server: Server;

  /**
   * Setup the RPC server used to communicate with the Hypothesis client.
   */
  constructor({ allowedOrigins, authToken, clientConfig }: ClientRPCOptions) {
    super();
    this._server = new Server(allowedOrigins);

    // A conservative estimate of when the grant token was issued.
    // When this is older than the true value, the frontend will just consider it
    // to "expire" earlier than it really does.
    const issuedAt = Date.now() - 30 * 1000;
    let grantToken = new JWT(clientConfig.services[0].grantToken, issuedAt);

    // Handle the requests for configuration from the Hypothesis client.
    this._server.register('requestConfig', async () => {
      if (grantToken.hasExpired()) {
        const issuedAt = Date.now();
        try {
          const response = await apiCall<{ grant_token: string }>({
            authToken,
            path: '/api/grant_token',
          });
          grantToken = new JWT(response.grant_token, issuedAt);
        } catch (err) {
          throw new Error(
            'Unable to fetch Hypothesis login. Please reload the assignment.',
          );
        }
      }

      clientConfig.services[0].grantToken = grantToken.value();
      return clientConfig;
    });

    this._server.register(
      'reportActivity',
      (eventType: AnnotationEventType, data: AnnotationEventData) => {
        this.emit('annotationActivity', eventType, data);
      },
    );

    this._server.register('openDashboard', () => {
      console.log('Open dashboard');
    });

    this._resolveGroups = () => {};
    const groups = new Promise(resolve => {
      this._resolveGroups = resolve;
    });

    // Handle the request for the list of groups to display from the Hypothesis
    // client.
    //
    // Determining the list of groups to display may take time on the backend
    // due to potentially slow calls to the external LMS to determine which course
    // section the user is in. Therefore we separate the request for the rest of
    // the Hypothesis client configuration from the request for the groups to
    // show. This enables the client to do most of its startup before the
    // group list is available.
    this._server.register('requestGroups', () => groups);
  }

  /**
   * Set which groups are available to select in the client.
   *
   * This method should be called exactly once during the LTI launch and calling
   * it a second time will have no effect.
   */
  setGroups(groups: string[]) {
    this._resolveGroups(groups);
  }

  /**
   * Set which user is focused in the client or none if `user` is `null`.
   *
   * This may be called any number of times.
   *
   * @param groups - Array of `groupid`s representing the focused user's groups
   */
  async setFocusedUser(user: User | null, groups: string[] | null) {
    await this._callClient('changeFocusModeUser', {
      // Passing `undefined` as the `username` disables focus mode in the client.
      //
      // TODO: The `username` property is deprecated in the client and should be
      // changed to `userid` once the client no longer references `username`.
      username: user ? user.userid : undefined,
      displayName: user ? user.displayName : undefined,
      groups: groups ?? undefined,
    });
  }

  /**
   * Instruct the client to show a content information banner.
   *
   * @param info - Data to show in the banner
   */
  async showContentInfo(info: ContentInfoConfig) {
    await this._callClient('showContentInfo', info);
  }

  /**
   * Make an RPC request to the client.
   */
  async _callClient(method: string, ...args: unknown[]) {
    const sidebar = await this._server.sidebarWindow;
    return rpcCall(sidebar.frame, sidebar.origin, method, args);
  }
}
