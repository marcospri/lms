import { mount } from 'enzyme';

import ChapterList from '../ChapterList';

describe('ChapterList', () => {
  const chapterData = [
    {
      title: 'Chapter One',
      level: 1,
      page: '10',
    },
    {
      title: 'Chapter Two',
      level: 1,
      page: '20',
    },
    {
      title: 'Chapter Two - Part 1',
      level: 2,
      page: '20',
    },
  ];
  const noop = () => {};
  const renderChapterList = (props = {}) =>
    mount(
      <ChapterList
        chapters={chapterData}
        selectedChapter={null}
        onSelectChapter={noop}
        onUseChapter={noop}
        {...props}
      />
    );

  describe('initial focus', () => {
    let container;

    beforeEach(() => {
      container = document.createElement('div');
      document.body.appendChild(container);
    });

    afterEach(() => {
      container.remove();
    });

    it('focuses the URL text input element', () => {
      const beforeFocused = document.activeElement;

      const wrapper = mount(
        <ChapterList
          chapters={chapterData}
          selectedChapter={null}
          onSelectChapter={noop}
          onUseChapter={noop}
        />,
        {
          attachTo: container,
        }
      );

      const focused = document.activeElement;
      const table = wrapper
        .find('table[data-testid="chapter-table"]')
        .getDOMNode();

      assert.notEqual(beforeFocused, focused);
      assert.equal(focused, table);
    });
  });

  it('renders chapter titles', () => {
    const chapterList = renderChapterList();
    const rows = chapterList.find('tbody tr');
    assert.equal(rows.length, chapterData.length);
    assert.equal(rows.at(0).find('td').at(0).text(), chapterData[0].title);
    assert.equal(rows.at(0).find('td').at(1).text(), chapterData[0].page);

    const tocLevels = [
      rows.at(0).find('[data-testid="toc-indent"]').prop('data-level'),
      rows.at(1).find('[data-testid="toc-indent"]').prop('data-level'),
      rows.at(2).find('[data-testid="toc-indent"]').prop('data-level'),
    ];
    assert.deepEqual(tocLevels, [0, 0, 1]);
  });

  [true, false].forEach(isLoading => {
    it('shows loading indicator in table if chapters are being fetched', () => {
      const chapterList = renderChapterList({ isLoading });
      assert.equal(chapterList.find('DataTable').prop('loading'), isLoading);
    });
  });

  it('calls `onSelectChapter` callback when a chapter is selected', () => {
    const onSelectChapter = sinon.stub();
    const chapterList = renderChapterList({ onSelectChapter });

    chapterList.find('DataTable').prop('onSelectRow')(chapterData[0]);

    assert.calledWith(onSelectChapter, chapterData[0]);
  });

  it('calls `onUseChapter` callback when a chapter is double-clicked', () => {
    const onUseChapter = sinon.stub();
    const chapterList = renderChapterList({ onUseChapter });

    chapterList.find('DataTable').prop('onConfirmRow')(chapterData[0]);

    assert.calledWith(onUseChapter, chapterData[0]);
  });
});
