-- Show the current status of the talk.
create or replace view all_proposals
as

with plus_1_votes as
(
    select proposal_id, count(*)
    from reviews_latestvote
    where vote = '+1'
    group by proposal_id
),

plus_0_votes as
(
    select proposal_id, count(*)
    from reviews_latestvote
    where vote = '+0'
    group by proposal_id
),

minus_0_votes as
(
    select proposal_id, count(*)
    from reviews_latestvote
    where vote = '−0'
    group by proposal_id
),

minus_1_votes as
(
    select proposal_id, count(*)
    from reviews_latestvote
    where vote = '−1'
    group by proposal_id
),

agg_score as
(
    select proposal_id,
    count(*) as total_votes,
    sum(
        case when vote = '+1' then 1
        when vote = '+0' then 0
        when vote = '−0' then 0
        when vote = '−1' then -1
        end) as agg_score
    from reviews_latestvote
    group by proposal_id
)

select
ppb.id,
ppb.title,
spkr.name as speaker,
case
when ppk.name = 'Short Talk (20 minutes)' then 0.5
when ppk.name = 'Talk (40 minutes)' then 1.0
when ppk.name = 'Tutorial (110 minutes)' then 2.0
end as talk_length,

coalesce(plus_1_votes.count, 0) as plus_1_votes,

100 * coalesce(plus_1_votes.count, 0) / agg_score.total_votes as approval_rating,

agg_score.total_votes,
agg_score.agg_score,
ppk.name as kind_of_talk,
coalesce(plus_0_votes.count, 0) as plus_0_votes,
coalesce(minus_0_votes.count, 0) as minus_0_votes,
coalesce(minus_1_votes.count, 0) as minus_1_votes,

rpr.status

from proposals_proposalbase ppb

join speakers_speaker spkr
on ppb.speaker_id = spkr.id

join proposals_proposalkind ppk
on ppb.kind_id = ppk.id

left join plus_1_votes
on ppb.id = plus_1_votes.proposal_id

left join plus_0_votes
on ppb.id = plus_0_votes.proposal_id

left join minus_0_votes
on ppb.id = minus_0_votes.proposal_id

left join minus_1_votes
on ppb.id = minus_1_votes.proposal_id

left join agg_score
on ppb.id = agg_score.proposal_id

left join reviews_proposalresult rpr
on ppb.id = rpr.proposal_id

where ppk.name != 'Open Space'

and rpr.status != 'rejected'

order by 5 desc, 6 desc, 8 desc
;