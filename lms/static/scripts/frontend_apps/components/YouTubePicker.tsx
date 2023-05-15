import { Button, CheckIcon, ModalDialog } from '@hypothesis/frontend-shared';
import { useRef, useState } from 'preact/hooks';

import { useYouTubeVideoInfo, videoIdFromYouTubeURL } from '../utils/youtube';
import URLFormWithPreview from './URLFormWithPreview';

export type YouTubePickerProps = {
  /** The initial value of the URL input field. */
  defaultURL?: string;

  onCancel: () => void;
  /** Callback invoked with the entered URL when the user accepts the dialog */
  onSelectURL: (url: string) => void;
};

export default function YouTubePicker({
  onCancel,
  defaultURL,
  onSelectURL,
}: YouTubePickerProps) {
  const inputRef = useRef<HTMLInputElement | null>(null);
  const [videoId, setVideoId] = useState(
    (defaultURL && videoIdFromYouTubeURL(defaultURL)) || null
  );
  const [error, setError] = useState<string>();
  const { thumbnail, metadata } = useYouTubeVideoInfo(videoId);

  const verifyURL = (inputURL: string) => {
    if (!inputURL) {
      setVideoId(null);
      setError(undefined);
      return;
    }

    const videoId = videoIdFromYouTubeURL(inputURL);
    if (videoId) {
      setVideoId(videoId);
      setError(undefined);
    } else {
      setVideoId(null);
      setError(
        'URL must be a YouTube video, e.g. "https://www.youtube.com/watch?v=cKxqzvzlnKU"'
      );
    }
  };
  const confirmSelection = () => {
    if (videoId) {
      onSelectURL(`youtube://${videoId}`);
    }
  };

  return (
    <ModalDialog
      title="Select YouTube video"
      onClose={onCancel}
      initialFocus={inputRef}
      size="lg"
      scrollable={false}
      buttons={[
        <Button data-testid="cancel-button" key="cancel" onClick={onCancel}>
          Cancel
        </Button>,
        <Button
          data-testid="select-button"
          disabled={!videoId}
          key="submit"
          onClick={confirmSelection}
          variant="primary"
        >
          Continue
        </Button>,
      ]}
    >
      <URLFormWithPreview
        label="Enter the URL of a YouTube video:"
        urlPlaceholder="e.g. https://www.youtube.com/watch?v=cKxqzvzlnKU"
        confirmBtnTitle="Confirm URL"
        onURLChange={verifyURL}
        error={error}
        inputRef={inputRef}
        defaultURL={defaultURL}
        thumbnail={thumbnail ?? { orientation: 'landscape' }}
      >
        {metadata && (
          <div className="flex flex-row space-x-2" data-testid="selected-video">
            <CheckIcon className="text-green-success" />
            <div className="grow font-bold italic">
              {metadata.title} ({metadata.channel})
            </div>
          </div>
        )}
      </URLFormWithPreview>
    </ModalDialog>
  );
}
