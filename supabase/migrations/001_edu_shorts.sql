create table if not exists public.short_jobs (
  id uuid primary key,
  user_id uuid not null references auth.users(id),
  slug text not null unique,
  title text not null,
  audience text not null,
  duration_seconds integer not null check (duration_seconds between 60 and 75),
  source_paths jsonb not null,
  status text not null check (status in ('queued', 'running', 'passed', 'needs_user_review', 'failed')),
  result_path text,
  error text,
  created_at timestamptz not null default now(),
  started_at timestamptz,
  finished_at timestamptz
);

alter table public.short_jobs enable row level security;

create policy "users read their jobs" on public.short_jobs
  for select using (auth.uid() = user_id);

create or replace function public.claim_next_short_job()
returns setof public.short_jobs
language plpgsql
security definer
set search_path = public
as $$
declare claimed public.short_jobs;
begin
  select * into claimed from public.short_jobs
  where status = 'queued'
  order by created_at
  for update skip locked
  limit 1;
  if found then
    update public.short_jobs
      set status = 'running', started_at = now()
      where id = claimed.id
      returning * into claimed;
    return next claimed;
  end if;
  return;
end;
$$;

create policy "users upload own source files" on storage.objects
  for insert to authenticated
  with check (
    bucket_id = 'short-sources'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );

create policy "users view own source files" on storage.objects
  for select to authenticated
  using (
    bucket_id = 'short-sources'
    and (storage.foldername(name))[1] = (select auth.uid()::text)
  );
