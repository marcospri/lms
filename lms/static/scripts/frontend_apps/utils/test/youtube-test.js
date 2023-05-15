import { videoIdFromYouTubeURL } from '../youtube';

describe('youtube', () => {
  describe('videoIdFromYouTubeURL', () => {
    [
      { url: 'https://youtu.be/cKxqzvzlnKU', expectedId: 'cKxqzvzlnKU' },
      { url: 'https://www.youtube.com/watch?v=123', expectedId: '123' },
      {
        url: 'https://www.youtube.com/watch?channel=hypothesis&v=foo',
        expectedId: 'foo',
      },
      {
        url: 'https://www.youtube.com/embed/embeddedId',
        expectedId: 'embeddedId',
      },
      {
        url: 'https://www.youtube.com/shorts/shortId',
        expectedId: 'shortId',
      },
      {
        url: 'https://www.youtube.com/live/liveId?feature=share',
        expectedId: 'liveId',
      },
    ].forEach(({ url, expectedId }) => {
      it('resolves ID from valid YouTube video', () => {
        assert.equal(videoIdFromYouTubeURL(url), expectedId);
      });
    });

    [
      'foo',
      'file://foo',
      'https://example.com',
      'https://youtube.com/watch',
      'https://youtu.be',
    ].forEach(url => {
      it('returns null for invalid YouTube videos', () => {
        assert.isNull(videoIdFromYouTubeURL(url));
      });
    });
  });
});
