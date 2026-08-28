import type { CompanyResult } from '../types';
import { AlignmentGridView } from './AlignmentGridView';

export function CompanyCard({ result }: { result: CompanyResult }) {
  const { company, alignment } = result;
  return (
    <article className='rounded-[10px] border border-(--border) p-4'>
      <header className='flex items-baseline justify-between gap-2'>
        <h3 className='m-0 text-base'>
          {company.website ? (
            <a
              className='text-(--text-h) no-underline hover:underline'
              href={company.website}
              target='_blank'
              rel='noreferrer'>
              {company.name}
            </a>
          ) : (
            company.name
          )}
        </h3>
        <span className='text-xs whitespace-nowrap text-(--text)'>
          {company.batch} · {company.status}
        </span>
      </header>
      <p className='mt-2 mb-3 text-sm text-(--text)'>Summary: {company.one_liner}</p>
      <AlignmentGridView grid={alignment} />
    </article>
  );
}
