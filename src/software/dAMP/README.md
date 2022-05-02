# Domain Analysis Machine Programming (dAMP)


@startuml
digraph FlowDiagram {
Event -> Telemetry_Registration
Telemetry_Registration -> Rapid_Evaluation
Rapid_Evaluation -> Triage
Triage -> Classification
Classification -> Healthy
Classification -> Signature_Label
Healthy -> Predict
Predict -> Signature_Label
Signature_Label -> Known
Signature_Label-> Unknown
Known -> Fast_Track_Treatment_Plan
Unknown -> Domain_Context_Analysis
Fast_Track_Treatment_Plan -> Action_Required
Action_Required -> Mitigation
Action_Required -> Human_AI_Update
Mitigation -> Fin
Mitigation -> Event
Domain_Context_Analysis -> Fin
Domain_Context_Analysis -> Human_AI_Update
Human_AI_Update -> Fin
Fin -> Event
} 
@enduml

## File: triage.py
High level classification of the state space of the data provided. 
Typically, we use this to understand the health state of the device from the telemetry package.

## File: 