import {
  Card,
  CardContent,
  DataTable,
  type DataTableProps,
  Link,
  useOrderedRows,
} from '@hypothesis/frontend-shared';
import { useMemo, useState } from 'preact/hooks';
import { useParams, Link as RouterLink } from 'wouter-preact';

import type {
  AssignmentStats,
  BaseDashboardStats,
  Course,
} from '../../api-types';
import { useConfig } from '../../config';
import { useAPIFetch } from '../../utils/api';
import { formatDateTime } from '../../utils/date';
import { replaceURLParams } from '../../utils/url';

type FlatAssignmentStats = BaseDashboardStats &
  Pick<AssignmentStats, 'title' | 'id'>;

export default function CourseAssignmentsActivity() {
  const { courseId } = useParams<{ courseId: string }>();
  const { dashboard } = useConfig(['dashboard']);
  const { routes } = dashboard;
  const course = useAPIFetch<Course>(
    replaceURLParams(routes.course, { course_id: courseId }),
  );
  const assignments = useAPIFetch<AssignmentStats[]>(
    replaceURLParams(routes.course_assignment_stats, {
      course_id: courseId,
    }),
  );

  const [order, setOrder] = useState<
    NonNullable<DataTableProps<FlatAssignmentStats>['order']>
  >({
    field: 'title',
    direction: 'ascending',
  });
  const flatAssignments: FlatAssignmentStats[] = useMemo(
    () =>
      (assignments.data ?? []).map(({ id, title, stats }) => ({
        id,
        title,
        ...stats,
      })),
    [assignments.data],
  );
  const orderedAssignments = useOrderedRows(flatAssignments, order);

  return (
    <Card>
      <CardContent>
        <h2 className="text-brand mb-3 text-xl" data-testid="title">
          {course.isLoading && 'Loading...'}
          {course.error && 'Could not load course title'}
          {course.data && course.data.title}
        </h2>
        <DataTable
          grid
          striped={false}
          emptyMessage={
            assignments.error
              ? 'Could not load assignments'
              : 'No assignments found'
          }
          title={course.data?.title ?? 'Loading...'}
          rows={orderedAssignments}
          columns={[
            { field: 'title', label: 'Assignment', classes: 'w-[60%]' },
            { field: 'annotations', label: 'Annotations' },
            { field: 'replies', label: 'Replies' },
            { field: 'last_activity', label: 'Last Activity' },
          ]}
          renderItem={(stats, field) => {
            if (['annotations', 'replies'].includes(field)) {
              return <div className="text-right">{stats[field]}</div>;
            } else if (field === 'title') {
              return (
                <RouterLink href={`/assignment/${stats.id}`} asChild>
                  <Link>{stats.title}</Link>
                </RouterLink>
              );
            }

            return (
              stats.last_activity &&
              formatDateTime(new Date(stats.last_activity))
            );
          }}
          loading={assignments.isLoading}
          orderableColumns={[
            'title',
            'annotations',
            'replies',
            'last_activity',
          ]}
          order={order}
          onOrderChange={setOrder}
        />
      </CardContent>
    </Card>
  );
}
