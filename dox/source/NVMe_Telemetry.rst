Telemetry Focused Summary
=========================
Intel devices with the Telemetry system reduce the total cost of ownership associated with support services differentiating our ecosystem from competition. Our Telemetry process adheres to the NVMe 1.3 and SATA ACS 4 standard definitions; enabling customers (OEMs) to deploy a diverse portfolio of products with a common methodology to arbitrate a variety of devices in the field.

The two functionalities introduce are host-initiated telemetry asynchronous event notification (HiTaC) and controller-initiated telemetry asynchronous event notification (CiTaC). HiTAC allows the host platform to requests persistent Metadata on-demand for monitoring operational feats such as: health, performance, quality of service, etc. The CiTaC enables the device to notify the host of OEM significant events requiring analysis to ensure product stability. The Meta data is dynamic and customized based on the operational events transpiring. These are further enabled by a novel auto decoding/translation of the Telemetry data sections without the requirement of proprietary and/or trade secret apparatuses such as internal tool chains. The procedure is so effective that the telemetry has absorbed and consolidated all data dumps within the system reducing complexity. The vision of telemetry is that the data provided alone can drive high confidence triage techniques to automatically locate, mark, characterize the fault, predict, detect anomalies, etc. Using our methods, the resources to resolve are significantly reduced, thereby focusing efforts on future products.

Mechanisms Architected for Success
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
The mechanisms within telemetry are architected so engineers can:
    - Aid in characterization of the system setup, usage, and the sequence to the fault event.
    - Diligently develop a problem statement using the scientific method by reducing scope.
    - When a fault case is not clear provide feedback for how we can improve the methodology in future engagements.
    - Improve the fault analysis handbook with encountered evaluations.
    - Save all data critical data using available tools.
    - Verify content.
    - Provided concise list of telemetry data included.

Specifications Supported
~~~~~~~~~~~~~~~~~~~~~~~~
Intel has decided to use the NVMe 1.3 Telemetry specification as a basis for all products (including SATA products based on ACS 4 definitions).

NVMe 1.3 Telemetry Specification
    - Host Initiated Telemetry Log (log page identifier 0x07)
    - Controller Initiated Telemetry Log (log page identifier 0x08).
SATA ACS 4 Definitions
    - Current Device Internal Status Data Log (log address 0x24)
    - Saved Device Internal Status Data Log (log address 0x25).

The both Telemetry specification defines that the page return data contains:
- Standard header specified
- Data requested must be multiple of 512 Bytes
- Up to three consecutive data areas as defined by Intel. There are not part of the standard.
- We defined what internal data needs to be packaged into the telemetry data sets.
- The data list, values, and details are dynamic so the content can be customized per usage.

Telemetry Key Command Information
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
NVMe
    - Identify controller data structure (ICDS; support of host and controller telemetry)
    - Asynchronous event Configuration (AEC; host enablement of the (H/C)iTaC event notifications) feature identifier 0Bh
    - Asynchronous event information notice (AEIN; detection field if telemetry log changed)
    - Log page identifiers (LPI; 07h host, 08h controller)
    - Create Host-Initiated Data (CHID; create a non-volatile snapshot of the telemetry data)
    - Get log page (GLP; access information to the log page payloads)
SATA
    - Identify controller data structure (ICDS; support of host and controller telemetry)
    - Log Address(LA; 24h host initiated, 25h device initiated)
    - Create Host-Initiated Data (CHID; create a non-volatile snapshot of the telemetry data)
    - Read Log Ext (PIO) / Read Log DMA Ext (LA; access information to the log page payloads)

Summary of Specification Divergence
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
NVMe
    - Telemetry is a non-blocking administration commands so other data command can occur.
    - No other administration commands can be sent until the request is processed, per our transport architecture.
    - Asynchronous event Request (AER) notification means the device can inform the host.
    - The snapshot must be kept in a state value of 0x1. HI log per spec is regenerated anytime Create = 1 or there is a reset. The retain AER only applies to the CI log.

SATA ACS-4
    - Telemetry is a blocking administration command so no other data can occur.
    - No other command on the device can be sent until the command is processed.
    - There is no AER (Asynchronous event Request) notification mechanism to inform the host if the drive has a Controller/ Device Initiated Telemetry (i.e. Event dump). Thus, the host has to request HIT or CIT header to see if data is available since the flags indicate the same content.
    - The CIT log is cleared once the last block is read.

Type Meta Expectation
~~~~~~~~~~~~~~~~~~~~~
Controller Initiated Telemetry (CiTAC)
    - Controller initiates a Get Log Page (NVMe 0x08, SATA 0x25) on internal minor or major issue is detected (such as: event dump or assert dump) . Most other dynamic data is not current after a dump.
    - Always provides a single data area (up to 31.9MB)

Host Initiated Telemetry (HiTAC)
    - Host initiates a Telemetry data log file containing Data Areas (DA) 1-3 supported
    - Controller initiated is driven by either an event or Assert; which will be in the HIT if pulled.

Generalized Cases
~~~~~~~~~~~~~~~~~~
    - System Fault Event Trigger Stop (General Case)
        - Software Assert, Event, and/or Hardware freeze.
        - Recommendation: Controller or Host Initiated generally get most of the data
    - System Healthy with silent fault.
        - Detected host side verification fault
        - Recommendation: Trigger Event dump snapshot and Host Initiated
    - Precondition: System Fault Trigger a stop for incompatibility
        - Recommendation: Trigger Event dump snapshot before update commit, then if fault occurs controller initiated
    - System healthy with system at reduced potential resources. I.E. Garbage collection
        - Recommendation: Trigger Event dump snapshot, periodically trigger host initiated on data area 1 and 2 to get analytics including historical time series progression.

Customer/Developer Data Object Addition Process for Code
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
    - Review Security Guidelines for Data Control
        - Determine if the data meets the guidelines
    - Contact representatives
    - Schedule Telemetry Working Group Meeting
    - Presentation
        - Usage Development and/or Business requisite
        - Review Control/Data Flow (C/DFG) and Data of the Object Desired
        - Showcase the usage and impact
        - Provide urgency of deployment and stakeholders
        - Timeline for internal and/or external release
        - Domain Reviewers
    - Allocate eUID to Sync Across products
    - Verify telemetry swim lane functionality and auto generation parser functionality with trackable tidbits link
    - Allocate Time
        - Live code review
        - Data extraction demonstration by walking through the C/DFG code path in Debugger
    - Request Code Promotion
        - Once code pushed, dispatch notification to stakeholders