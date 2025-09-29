with events as (
    select * from {{ ref('stg_events') }}
),
users as (
    select * from {{ ref('stg_users') }}
)

select
    e.user_id,
    u.country,
    e.occurred_on as activity_date,
    count(*) filter (where e.event_type = 'session_start') as sessions_started,
    count(*) filter (where e.event_type = 'session_end')   as sessions_ended,
    count(*) filter (where e.event_type = 'purchase')      as purchases,
    max(case when e.event_type = 'purchase' then 1 else 0 end) as made_purchase,
    bool_or(u.is_recent) as is_recent_user
from events e
join users u on e.user_id = u.user_id
group by 1,2,3
