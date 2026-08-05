# Recording Assessment v2

## Project
VoiceOfOpenDoor

## Assessment Date
July 28, 2026

## Scope
Extends Recording Assessment v1. Covers the 4 recordings added in this session that were not part of the original 16-file corpus. All 20 recordings are now archived as originals in `Dataset/Raw Audio/`.

## Carried Forward From v1 (Unresolved)

The following remain outstanding from v1 and are not resolved by this document:

- Editedaudio1407063783.m4a — peak level near maximum; audible distortion not yet confirmed.
- Editedaudio1948085081.m4a — comparatively weaker estimated SNR; not yet listened for room noise.
- Editedaudio2655457179.m4a — comparatively lower estimated SNR; not yet listened for background/room tone.
- Verified transcripts still do not exist for any recording (Phase 5 blocker, unaffected by this document).

## New Recordings

### RecUpVoiceOfOpenDoorTest.mp3

- Source: RecUp recording app test
- Equipment: Pending — not yet documented
- Environment: Pending — not yet documented
- Background noise: No significant disqualifying noise observed.
- Consistency: Consistent speaking level.
- Speech quality: Natural conversational speech.
- Duration: 6 minutes 31 seconds
- Content: Spoken summary of the VoiceOfOpenDoor project
- Corpus suitability: Candidate. Longest single recording in the corpus; requires segmentation before use as multiple corpus entries rather than one.
- Engineering recommendation: **Retain for corpus. Segment before training.**
- Recommendation basis: Subjective listening assessment completed and confirmed July 27-28, 2026. Equipment and environment detail were not part of that review and remain undocumented, but that does not block the corpus-suitability conclusion above.

### RecUpAppTest Recording.mp3

- Duration: 17.6 seconds
- Engineering recommendation: **Rejected.**
- Reason: Audible radio.
- Recommendation: Do not use for corpus.
- Recommendation basis: Subjective listening assessment completed and confirmed July 27-28, 2026. The stated reason is sufficient on its own; no further equipment or environment detail is needed for this call.

### VictorStreamTestNoHeadPhones.mp3

- Source: Unconfirmed — filename suggests a HumanWare Victor Reader Stream recording-method comparison, without headphones. Not yet confirmed by Dean.
- Equipment: Unconfirmed
- Environment: Unconfirmed
- Background noise: Not yet assessed
- Consistency: Not yet assessed
- Speech quality: Not yet assessed
- Duration: 10.5 seconds
- Corpus suitability: Undetermined
- Engineering recommendation: **Evaluation Only**
- Reason: Purpose of this recording has not been confirmed. Do not classify as Candidate or Rejected until it is confirmed whether this is intended as corpus material or an equipment test.

### VRStreamHeadphone.mp3

- Source: Unconfirmed — filename suggests a HumanWare Victor Reader Stream recording-method comparison, with headphones. Not yet confirmed by Dean.
- Equipment: Unconfirmed
- Environment: Unconfirmed
- Background noise: Not yet assessed
- Consistency: Not yet assessed
- Speech quality: Not yet assessed
- Duration: 17.3 seconds
- Technical note: Bitrate (32 kbps) is notably lower than all other recordings in the corpus (~80-96 kbps), suggesting a different source or compression setting.
- Corpus suitability: Undetermined
- Engineering recommendation: **Evaluation Only**
- Reason: Purpose of this recording has not been confirmed. Do not classify as Candidate or Rejected until it is confirmed whether this is intended as corpus material or an equipment test.

## Current Recommendation

Dataset Status

- Ready for transcription: Partially — RecUpVoiceOfOpenDoorTest.mp3 is a Candidate pending segmentation; the original 16 remain as stated in v1.
- Ready for training: No.

Priority Next Steps

1. Confirm the purpose of VictorStreamTestNoHeadPhones.mp3 and VRStreamHeadphone.mp3.
2. Backfill the Pending fields for the two RecUp recordings (equipment, environment, background noise, consistency, speech quality) so the Candidate/Rejected calls are fully documented, not just concluded.
3. Resolve the three recordings carried forward from v1 that still require listening review.
4. Stand up the Speech Processing Pipeline (`Tools/Audio Processing/`) on the Windows 11 reference platform so future transcription and segmentation does not depend on manual review per recording.
