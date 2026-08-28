export const FACET_NAMES = ['customer', 'problem', 'mechanism', 'wedge', 'business_model'] as const
export type FacetName = (typeof FACET_NAMES)[number]

export interface Company {
  id: number
  name: string
  one_liner: string
  long_description: string
  website: string
  batch: string
  status: string
  stage: string
  team_size: number
  [key: string]: unknown
}

export interface AlignmentCell {
  idea_value: string
  company_value: string
  same: boolean
}

export type AlignmentGrid = Record<FacetName, AlignmentCell>

export interface CompanyResult {
  company: Company
  alignment: AlignmentGrid
  score: number
}

export interface QueryResult {
  companies: CompanyResult[]
  whitespace: Record<FacetName, string[]>
}

export interface CannedExample {
  id: string
  idea_text: string
  result: QueryResult
}
