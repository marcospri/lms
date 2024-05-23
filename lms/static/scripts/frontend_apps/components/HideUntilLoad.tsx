import { Spinner } from '@hypothesis/frontend-shared';
import classnames from 'classnames';
import type { ComponentChildren } from 'preact';
import { useCallback, useMemo, useRef, useState } from 'preact/hooks';

import { InitialLoadingContext } from '../utils/initial-loading-context';

export type InitialLoadingProps = {
  children: ComponentChildren;
  classes?: string | string[];
};

export default function HideUntilLoad({
  children,
  classes,
}: InitialLoadingProps) {
  const [initialLoadInProgress, setInitialLoadInProgress] = useState(true);
  const loadingInstances = useRef(new Set<string>());

  const startLoading = useCallback(
    (key: string) => loadingInstances.current.add(key),
    [],
  );
  const finishLoading = useCallback((key: string) => {
    loadingInstances.current.delete(key);
    // We consider loading is in progress as long as there are loading
    // instances.
    // Also, once we have transitioned from true to false once, we don't want
    // to go back to true ever again, considering the initial load has finished.
    setInitialLoadInProgress(prev => prev && loadingInstances.current.size > 0);
  }, []);
  const contextValue = useMemo(
    () => ({ startLoading, finishLoading }),
    [finishLoading, startLoading],
  );

  return (
    <InitialLoadingContext.Provider value={contextValue}>
      {initialLoadInProgress && (
        <div
          className={classnames(
            'flex items-center justify-center bg-white/50',
            classes,
          )}
        >
          <Spinner size="lg" />
        </div>
      )}
      <div
        className={classnames(classes, {
          hidden: initialLoadInProgress,
        })}
      >
        {children}
      </div>
    </InitialLoadingContext.Provider>
  );
}
