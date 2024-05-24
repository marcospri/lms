import type { DataTableProps } from '@hypothesis/frontend-shared';
import { DataTable } from '@hypothesis/frontend-shared';
import { useOrderedRows } from '@hypothesis/frontend-shared';
import { useMemo, useState } from 'preact/hooks';

import type { BaseDashboardStats } from '../../api-types';

export type OrderableActivityTableProps<T extends BaseDashboardStats> = Pick<
  DataTableProps<T>,
  'emptyMessage' | 'rows' | 'renderItem' | 'loading' | 'title'
> & {
  columnNames: Partial<Record<keyof T, string>>;
  initialOrderField: keyof T;
};

export default function OrderableActivityTable<T extends BaseDashboardStats>({
  initialOrderField,
  rows,
  columnNames,
  ...restOfTableProps
}: OrderableActivityTableProps<T>) {
  const [order, setOrder] = useState<NonNullable<DataTableProps<T>['order']>>({
    field: initialOrderField,
    direction: 'ascending',
  });
  const orderedRows = useOrderedRows(rows, order);
  const columns = useMemo(
    () =>
      Object.entries(columnNames).map(([field, label], index) => ({
        field: field as keyof T,
        label: label as string,
        classes: index === 0 ? 'w-[60%]' : undefined,
      })),
    [columnNames],
  );

  return (
    <DataTable
      grid
      striped={false}
      columns={columns}
      rows={orderedRows}
      orderableColumns={Object.keys(columnNames) as Array<keyof T>}
      order={order}
      onOrderChange={setOrder}
      {...restOfTableProps}
    />
  );
}
