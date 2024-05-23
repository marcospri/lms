import classnames from 'classnames';
import { Route } from 'wouter-preact';

import HideUntilLoad from '../HideUntilLoad';
import DashboardFooter from './DashboardFooter';
import StudentsActivity from './StudentsActivity';

export default function DashboardApp() {
  return (
    <div className="flex flex-col min-h-screen bg-grey-2">
      <header
        className={classnames(
          'flex justify-center p-3 w-full',
          'bg-white border-b shadow',
        )}
      >
        <img
          alt="Hypothesis logo"
          src="/static/images/hypothesis-wordmark-logo.png"
          className="h-10"
        />
      </header>
      <HideUntilLoad classes="flex-grow">
        <div className="mx-auto max-w-6xl px-3 py-5">
          <Route path="/assignment/:assignmentId">
            <StudentsActivity />
          </Route>
        </div>
      </HideUntilLoad>
      <DashboardFooter />
    </div>
  );
}
