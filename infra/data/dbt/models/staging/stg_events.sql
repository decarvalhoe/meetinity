with source as (
    select * from {{ ref('events') }}
)

select
    cast(event_id as integer)             as event_id,
    cast(user_id as integer)              as user_id,
    lower(event_type)                     as event_type,
    cast(occurred_at as timestamp)        as occurred_at,
    date_trunc('day', cast(occurred_at as timestamp)) as occurred_on
from source
