import { CancelIcon, Input } from '@hypothesis/frontend-shared';
import type { Ref } from 'preact';

import { useUniqueId } from '../utils/hooks';

export type UrlPickerFormProps = {
  onSubmit: () => void;
  error?: string;
  urlPlaceholder: string;
  defaultURL?: string;
  'aria-label': string;
  inputRef?: Ref<HTMLElement | undefined>;
};

/**
 * A form that displays a single URL input, and optionally, an error
 */
export default function UrlPickerForm({
  onSubmit,
  error,
  urlPlaceholder,
  defaultURL,
  'aria-label': ariaLabel,
  inputRef,
}: UrlPickerFormProps) {
  const id = useUniqueId('url');
  const submit = (event: Event) => {
    event.preventDefault();
    onSubmit();
  };

  return (
    <>
      <form className="flex flex-row items-center space-x-2" onSubmit={submit}>
        <label htmlFor={id}>URL: </label>

        <Input
          aria-label={ariaLabel}
          classes="grow"
          defaultValue={defaultURL}
          hasError={!!error}
          elementRef={inputRef}
          name="url"
          placeholder={urlPlaceholder}
          required
          id={id}
        />
      </form>
      {/** setting a height here "preserves space" for this error display
       * and prevents the dialog size from jumping when an error is rendered */}
      <div
        className="h-4 flex flex-row items-center space-x-1 text-red-error"
        data-testid="error-message"
      >
        {!!error && (
          <>
            <CancelIcon />
            <div className="grow">{error}</div>
          </>
        )}
      </div>
    </>
  );
}
