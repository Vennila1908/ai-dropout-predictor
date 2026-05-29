# Future Scope

The current build is intentionally focused — predict, explain, recommend, log.
Below are the directions a follow-on team could pursue, ordered roughly by
feasibility.

## 1. Real-time Attendance via IoT

* RFID / NFC tap-in at lecture-hall doors → MQTT → backend ingest endpoint.
* Replaces the periodic CSV upload entirely.
* Push live attendance deltas to faculty dashboards via WebSocket.

## 2. Computer-vision Attendance

* Face-recognition camera at the door (on-device, e.g. Jetson Nano).
* Library: `face_recognition` or `insightface`.
* Privacy: store only template embeddings, never raw images. Opt-in only.

## 3. Emotion / Engagement Analysis

* Classroom camera or webcam during online sessions.
* Per-student engagement timeseries (`engaged | neutral | distracted`).
* Feed as a new feature `engagement_index_30d` into the ML model.

## 4. Voice Counseling Sessions

* Whisper.cpp transcribes counseling audio locally.
* Local LLM summarizes → autopopulates `counseling_sessions.notes`.
* Speaker diarization to separate counselor vs student voice.

## 5. WhatsApp / Parent Alerts

* High-risk → templated WhatsApp Business API or SMS notification to guardian.
* Configurable thresholds per department; opt-in per student.
* Audit-logged; rate-limited to one nudge per fortnight.

## 6. Native Mobile App

* React Native (or Expo) reusing the existing `features/*Api.ts` clients.
* Faculty quick-actions: take attendance, log a note, mark a follow-up.
* Push notifications for newly flagged students.

## 7. Predictive Semester Analysis

* Sequence model (LSTM / Temporal Fusion Transformer) that takes
  semester-by-semester history and projects the next semester's GPA + risk.
* Surfaces *trajectory* rather than a snapshot.

## 8. What-if Simulator

* Interactive panel: "If attendance improves to 85 %, what's the new risk?"
* Re-run the model client-side via ONNX export of the trained tree.

## 9. Group / Cohort Recommendations

* Cluster high-risk students by feature similarity (KMeans on engineered
  features).
* LLM proposes a *group* intervention plan per cluster.

## 10. ERP / SIS Integration

* Pull attendance + marks directly from existing institutional systems
  (SAP SLcM, Moodle, Canvas, Banner).
* Replaces the manual upload step entirely.

## 11. Multi-tenant SaaS Mode

* Per-college tenant isolation at the row + storage level.
* SSO via SAML / OIDC (Keycloak, Authentik).

## 12. Continuous Learning Loop

* Counselor feedback ("this prediction was wrong / right / partially right")
  is stored and used to retrain the model periodically.
* Drift detection: alert when feature distributions shift > 2σ.
