Phases of Fault Analysis
########################

Goal
    Disposition customers challenges to determine the paths for mitigation to reduce exposure. Intention characterizes asserts, fault, warnings, etc. in a way that we can understand the impact such that we can decide if there are opportunities to for phases below.

Phases of Analysis
-------------------
    #. Document encountered challenge and preconditions.
    #. Save meta data and state.
    #. Analyze conditions and operational path.
    #. Perform Scientific Process below.
    #. Provide recommendations from analysis on how to close architecture challenges.
        - Eliminate the assert or failure
        - Recommending handling to recover
        - Create path to fail gracefully
        - Refactor the logic to narrow the failure conditions
    #. Hypothesis of mitigation techniques.
    #. Empirical mitigation techniques impact to reduction or clarification of fault.

Scientific Process
~~~~~~~~~~~~~~~~~~~
    For first pass do not spend more than 20-30 minutes for evaluation. If the evaluation requires more information, seek out an expert or bring the gaps to the working group for acceleration of the item. Expectation is 1-3 other steps are a bonus.
        #. Make Observations
            #. View the origin of the condition and trace the path to current state.
            #. Understand and collect evidence, experiments, and correlation needed for usage. The process will involve understanding underlying mechanisms and system interactions to classify the failing case. The development of the failing case will involve understanding the control flow and data flow graph with the behavioral expectation to the error classification.
            #. The general failure condition will show a trace of valid conditions until one is not met in the flow such that the coverage of all cases are depicted in a manner such as Boolean algebra, truth tables, sequence diagrams, finite state machine (deterministic finite automata), etc.
            #. Clarify the focused experiment, cases, and predictions for the root cause. Gather data to conclusively replicate the failure or conditions that lead to such a situation.
            #. Define the problem.
        #. Think of Interesting questions
            #. Understand necessary analysis data.
            #. Identify paths for further investigation.
            #. Create a strong correlation in the concerning area.
        #. Formulate Hypotheses
            #. The developer will cultivate and expand a hypothesis on the finding to give exact clarity to confirm defect based on analysis and usage of data.
            #. Specify the requirements and identify variables violated in the defective case.
            #. When resources or strategies are exhausted create a brain storming session or working group to further understand failure to develop a collective hypothesis or explore mechanisms until a relevant formulation is reached. In the event, of a hard failure note it so further investigation can continue.
        #. Develop Testable Data and Predictions
            #. Based on evidence, investigate the fault area beginning to formulate a predictive mechanism or existence of defect in design.
            #. Refine, Alter, and Expand
                #. Upon proving the root cause of the failure, the developer will understand and propose solutions based on the architecture and implementation to address the concern and maintain future extensibility.
                #. Build a prototype to solution to test defective case proving solution definitively resolved the original defect.
                #. Before completing the solution, ensure the requirements are met and communicate results to technical lead, system technical product lead.
                #. The solution will follow the standards defined for the product library and appropriate reviews before promoting to live library testing.
        #. Refine, Alter, and Expand, or Reject
            #. After failure case resolution, communicate the resolution case where the solution will be tested in an independent controlled environment the failure was produced in confirming the solution is appropriate in the common product library.
        #. Accept
            #. Solution is determined to be adequate for test case and corresponding horizontal technical leads should be made aware of the item resolution.
            #. Follows to the solution that alter the architecture or expose failure conditions must be communicated to forward looking teams in a functional change in the ASIC, Firmware, Media, and or Tools.

Template of Documentation
~~~~~~~~~~~~~~~~~~~~~~~~~~
- Title: <Assert/Fault/Unique Signature Code>
- Description: High level module information for the corresponding code and processes of dependant items.
- Evaluation Focal Points
    #.	Evaluated Condition
        - Bullet list of conditions for event.
        - Source code soft link
    #.	Owner and Participant(s)
        - Developers and technical support members
    #.	Seen at Customer (Yes/No)
        - Classification if internal or external encountered challenge
    #.	Assert, Fault, Warning, Slient, etc. Condition Looseness or Ambiguity
        - Vagueness of the conditions around encountering event.
    #. Developer to do Analysis using “Scientific Process”
    #. Problem Statement
    #. Known causes
        - List of known classifications of causes
    #. Hardware/Firmware/Software Data Necessary for Analysis
        - List explicit annotated data structures
    #. Prevention recommendations
    #. Hardware-Firmware-Software Components
        - Links to code, architecture documents, versions, etc.
    #. Catastrophic Event leading to an Annual Failure Rate (AFR) post Reliability Demonstration Testing (RDT) (Yes/No) Why?
    #. Brown out or Power Loss Immanent (PLI) deadlock exposure (Yes/No) Why?
    #. Silent data error (SDE) or data miss-compare exposure (Yes/No) Why?
    #. Granularity of potential exposure to Silent Data Error Rate (SDER) (Yes/No) Why?
    #. Related items: <Assert/Fault/Unique Signature Code>
    #. Database items: Developer tracking system links

