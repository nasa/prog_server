# Prognostics As-A-Service (PaaS) Sandbox
[![CodeFactor](https://www.codefactor.io/repository/github/nasa/prog_server/badge)](https://www.codefactor.io/repository/github/nasa/prog_server)
[![GitHub License](https://img.shields.io/badge/License-NOSA-green)](https://github.com/nasa/prog_server/blob/master/license.pdf)
[![GitHub Releases](https://img.shields.io/github/release/nasa/prog_server.svg)](https://github.com/nasa/prog_server/releases)

The NASA Prognostics As-A-Service (PaaS) Sandbox is a simplified implementation of a Software Oriented Architecture (SOA) for performing prognostics (estimation of time until events and future system states) of engineering systems. The PaaS Sandbox is a wrapper around the [Prognostics Algorithms Package](https://github.com/nasa/prog_algs) and [Prognostics Models Package](https://github.com/nasa/prog_models), allowing one or more users to access the features of these packages through a REST API. The package is intended to be used as a research tool to prototype and benchmark Prognostics As-A-Service (PaaS) architectures and work on the challenges facing such architectures, including Generality, Communication, Security, Environmental Complexity, Utility, and Trust.

This is designed to be used with the [Prognostics Algorithms Package](https://github.com/nasa/prog_algs) and [Prognostics Models Package](https://github.com/nasa/prog_models).

## Installation - SOON
`pip install prog_server`

## [Documentation](https://nasa.github.io/prog_server/) - SOON
See documentation [here](https://nasa.github.io/prog_server/)

## Citing this repository
Use the following to cite this repository:

```
@misc{2021_nasa_prog_models,
    author    = {Christopher Teubert and Jason Watkins and Katelyn Jarvis},
    title     = {Prognostics As-A-Service (PaaS) Sandbox},
    month     = Jan,
    year      = 2022,
    version   = {1.0},
    url       = {https://github.com/nasa/prog_server}
    }
```

The corresponding reference should look like this:

C. Teubert, J. Watkins, K. Jarvis, Prognostics As-A-Service (PaaS) Sandbox, v1.0, Jan. 2022. URL https://github.com/nasa/prog_server.

## Notices

Copyright © 2021 United States Government as represented by the Administrator of the National Aeronautics and Space Administration.  All Rights Reserved.

## Disclaimers

No Warranty: THE SUBJECT SOFTWARE IS PROVIDED "AS IS" WITHOUT ANY WARRANTY OF ANY KIND, EITHER EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED TO, ANY WARRANTY THAT THE SUBJECT SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR FREEDOM FROM INFRINGEMENT, ANY WARRANTY THAT THE SUBJECT SOFTWARE WILL BE ERROR FREE, OR ANY WARRANTY THAT DOCUMENTATION, IF PROVIDED, WILL CONFORM TO THE SUBJECT SOFTWARE. THIS AGREEMENT DOES NOT, IN ANY MANNER, CONSTITUTE AN ENDORSEMENT BY GOVERNMENT AGENCY OR ANY PRIOR RECIPIENT OF ANY RESULTS, RESULTING DESIGNS, HARDWARE, SOFTWARE PRODUCTS OR ANY OTHER APPLICATIONS RESULTING FROM USE OF THE SUBJECT SOFTWARE.  FURTHER, GOVERNMENT AGENCY DISCLAIMS ALL WARRANTIES AND LIABILITIES REGARDING THIRD-PARTY SOFTWARE, IF PRESENT IN THE ORIGINAL SOFTWARE, AND DISTRIBUTES IT "AS IS."

Waiver and Indemnity:  RECIPIENT AGREES TO WAIVE ANY AND ALL CLAIMS AGAINST THE UNITED STATES GOVERNMENT, ITS CONTRACTORS AND SUBCONTRACTORS, AS WELL AS ANY PRIOR RECIPIENT.  IF RECIPIENT'S USE OF THE SUBJECT SOFTWARE RESULTS IN ANY LIABILITIES, DEMANDS, DAMAGES, EXPENSES OR LOSSES ARISING FROM SUCH USE, INCLUDING ANY DAMAGES FROM PRODUCTS BASED ON, OR RESULTING FROM, RECIPIENT'S USE OF THE SUBJECT SOFTWARE, RECIPIENT SHALL INDEMNIFY AND HOLD HARMLESS THE UNITED STATES GOVERNMENT, ITS CONTRACTORS AND SUBCONTRACTORS, AS WELL AS ANY PRIOR RECIPIENT, TO THE EXTENT PERMITTED BY LAW.  RECIPIENT'S SOLE REMEDY FOR ANY SUCH MATTER SHALL BE THE IMMEDIATE, UNILATERAL TERMINATION OF THIS AGREEMENT.
