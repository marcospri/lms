import {
  checkAccessibility,
  mockImportedComponents,
} from '@hypothesis/frontend-testing';
import { mount } from 'enzyme';

import StudentsActivity, { $imports } from '../StudentsActivity';

describe('StudentsActivity', () => {
  const defaultStudents = [
    {
      display_name: 'b',
      last_activity: '2020-01-01T00:00:00',
      annotations: 8,
      replies: 0,
    },
    {
      display_name: 'a',
      last_activity: '2020-01-02T00:00:00',
      annotations: 3,
      replies: 20,
    },
    {
      display_name: 'c',
      last_activity: '2020-01-02T00:00:00',
      annotations: 5,
      replies: 100,
    },
  ];

  beforeEach(() => {
    $imports.$mock(mockImportedComponents());
  });

  afterEach(() => {
    $imports.$restore();
  });

  function createComponent(props = {}) {
    return mount(
      <StudentsActivity
        assignment={props.assignment ?? { title: 'The title' }}
        students={props.students ?? defaultStudents}
      />,
    );
  }

  ['some title', 'foo bar'].forEach(title => {
    it('shows expected title', () => {
      const wrapper = createComponent({
        assignment: { title },
      });
      const titleElement = wrapper.find('[data-testid="title"]');
      const tableElement = wrapper.find('DataTable');
      const expectedTitle = `Assignment: ${title}`;

      assert.equal(titleElement.text(), expectedTitle);
      assert.equal(tableElement.prop('title'), expectedTitle);
    });
  });

  it('shows empty students message', () => {
    const wrapper = createComponent({
      students: [],
    });
    const tableElement = wrapper.find('DataTable');

    assert.equal(tableElement.prop('emptyMessage'), 'No students found');
  });

  [
    {
      orderToSet: { field: 'annotations', direction: 'descending' },
      expectedStudents: [
        {
          display_name: 'b',
          last_activity: '2020-01-01T00:00:00',
          annotations: 8,
          replies: 0,
        },
        {
          display_name: 'c',
          last_activity: '2020-01-02T00:00:00',
          annotations: 5,
          replies: 100,
        },
        {
          display_name: 'a',
          last_activity: '2020-01-02T00:00:00',
          annotations: 3,
          replies: 20,
        },
      ],
    },
    {
      orderToSet: { field: 'replies', direction: 'ascending' },
      expectedStudents: [
        {
          display_name: 'b',
          last_activity: '2020-01-01T00:00:00',
          annotations: 8,
          replies: 0,
        },
        {
          display_name: 'a',
          last_activity: '2020-01-02T00:00:00',
          annotations: 3,
          replies: 20,
        },
        {
          display_name: 'c',
          last_activity: '2020-01-02T00:00:00',
          annotations: 5,
          replies: 100,
        },
      ],
    },
    {
      orderToSet: { field: 'last_activity', direction: 'descending' },
      expectedStudents: [
        {
          display_name: 'a',
          last_activity: '2020-01-02T00:00:00',
          annotations: 3,
          replies: 20,
        },
        {
          display_name: 'c',
          last_activity: '2020-01-02T00:00:00',
          annotations: 5,
          replies: 100,
        },
        {
          display_name: 'b',
          last_activity: '2020-01-01T00:00:00',
          annotations: 8,
          replies: 0,
        },
      ],
    },
  ].forEach(({ orderToSet, expectedStudents }) => {
    it('orders students on order change', () => {
      const wrapper = createComponent();
      const getRows = () => wrapper.find('DataTable').prop('rows');
      const getOrder = () => wrapper.find('DataTable').prop('order');
      const setOrder = order => {
        wrapper.find('DataTable').props().onOrderChange(order);
        wrapper.update();
      };

      // Initially, students are ordered by name
      assert.deepEqual(getOrder(), {
        field: 'display_name',
        direction: 'ascending',
      });
      assert.deepEqual(getRows(), [
        {
          display_name: 'a',
          last_activity: '2020-01-02T00:00:00',
          annotations: 3,
          replies: 20,
        },
        {
          display_name: 'b',
          last_activity: '2020-01-01T00:00:00',
          annotations: 8,
          replies: 0,
        },
        {
          display_name: 'c',
          last_activity: '2020-01-02T00:00:00',
          annotations: 5,
          replies: 100,
        },
      ]);

      setOrder(orderToSet);
      assert.deepEqual(getOrder(), orderToSet);
      assert.deepEqual(getRows(), expectedStudents);
    });
  });

  [
    { fieldName: 'display_name', expectedValue: 'Jane Doe' },
    { fieldName: 'annotations', expectedValue: '37' },
    { fieldName: 'replies', expectedValue: '25' },
    { fieldName: 'last_activity', expectedValue: '2024-01-01 10:35' },
  ].forEach(({ fieldName, expectedValue }) => {
    it('renders every field as expected', () => {
      const studentStats = {
        display_name: 'Jane Doe',
        last_activity: '2024-01-01T10:35:18',
        annotations: 37,
        replies: 25,
      };
      const wrapper = createComponent();

      const item = wrapper
        .find('DataTable')
        .props()
        .renderItem(studentStats, fieldName);
      const value = typeof item === 'string' ? item : mount(item).text();

      assert.equal(value, expectedValue);
    });
  });

  it(
    'should pass a11y checks',
    checkAccessibility({
      content: () => createComponent(),
    }),
  );
});
