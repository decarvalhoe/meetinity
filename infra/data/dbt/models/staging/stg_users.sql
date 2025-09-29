with source as (
    select * from {{ ref('users') }}
)

select
    cast(user_id as integer)       as user_id,
    country,
    cast(created_at as date)       as created_at,
    created_at >= (current_date - INTERVAL '30' DAY) as is_recent
from source
