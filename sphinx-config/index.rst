Prognostics As-A-Service (PaaS) Sandbox
=============================================================

[![CodeFactor](https://www.codefactor.io/repository/github/nasa/prog_server/badge)](https://www.codefactor.io/repository/github/nasa/prog_server)
[![License](https://img.shields.io/badge/License-NOSA-green)](https://github.com/nasa/prog_algs/blob/master/license.pdf)
[![Releases](https://img.shields.io/github/release/nasa/prog_algs.svg)](https://github.com/nasa/prog_algs/releases)

The NASA Prognostics As-A-Service (PaaS) Sandbox (a.k.a., prog_server) is a simplified implementation of a Software Oriented Architecture (SOA) for performing prognostics (estimation of time until events and future system states) of engineering systems. The PaaS Sandbox is a wrapper around the `Prognostics Algorithms Package <https://github.com/nasa/prog_algs>`__ and `Prognostics Models Package <https://github.com/nasa/prog_models>`__, allowing one or more users to access the features of these packages through a REST API. The package is intended to be used as a research tool to prototype and benchmark Prognostics As-A-Service (PaaS) architectures and work on the challenges facing such architectures, including Generality, Communication, Security, Environmental Complexity, Utility, and Trust.

The PaaS Sandbox is actually two packages, prog_server and prog_client. The prog_server package is the server that provides the REST API. The prog_client package is the client that uses the REST API to access the server.

prog_server uses the `Prognostics Algorithms Package <https://github.com/nasa/prog_algs>`__ and `Prognostics Models Package <https://github.com/nasa/prog_models>`__.

The Prognostics As-A-Service (PaaS) Sandbox was developed by researchers of the NASA Prognostics Center of Excellence (PCoE) and `Diagnostics & Prognostics Group <https://www.nasa.gov/content/diagnostics-prognostics>`__.

The PaaS Sandbox is a simplified version of the Prognostics As-A-Service Architecture implented as the PaaS/SWS Safety Service software by the NASA System Wide Safety (SWS) project, building upon the original work of the Convergent Aeronautics Solutions (CAS) project. This implementation is a research tool, and is therefore missing important features that should be present in a full implementation of the PaaS architecture such as authentication and persistent state management.

If you are new to this package, see `getting started <getting_started.html>`__.

.. toctree::
   :maxdepth: 2

   getting_started
   load_ests
   prog_client
   Prog Server API <https://app.swaggerhub.com/apis-docs/teubert/prog_server>
   ProgModels <https://nasa.github.io/prog_models>
   ProgAlgs <https://nasa.github.io/prog_algs>
   dev_guide
   GitHub <https://github.com/nasa/prog_server>

Citing this repository
-----------------------
Use the following to cite this repository:

@misc{2022_nasa_prog_server,
  | author    = {Christopher Teubert and Jason Watkins and Katelyn Jarvis},
  | title     = {Prognostics As-A-Service (PaaS) Sandox},
  | month     = Jan,
  | year      = 2022,
  | version   = {1.0.0},
  | url       = {https://github.com/nasa/prog_server}
  | }

The corresponding reference should look like this:

C. Teubert, J. Watkins, K. Jarvis Prognostics As-A-Service (PaaS) Package, v1.0.0, Jan 2022. URL https://github.com/nasa/prog_server.

Indices and tables
-----------------------

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`

Disclaimers
----------------------

No Warranty: THE SUBJECT SOFTWARE IS PROVIDED "AS IS" WITHOUT ANY WARRANTY OF ANY KIND, EITHER EXPRESSED, IMPLIED, OR STATUTORY, INCLUDING, BUT NOT LIMITED TO, ANY WARRANTY THAT THE SUBJECT SOFTWARE WILL CONFORM TO SPECIFICATIONS, ANY IMPLIED WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE, OR FREEDOM FROM INFRINGEMENT, ANY WARRANTY THAT THE SUBJECT SOFTWARE WILL BE ERROR FREE, OR ANY WARRANTY THAT DOCUMENTATION, IF PROVIDED, WILL CONFORM TO THE SUBJECT SOFTWARE. THIS AGREEMENT DOES NOT, IN ANY MANNER, CONSTITUTE AN ENDORSEMENT BY GOVERNMENT AGENCY OR ANY PRIOR RECIPIENT OF ANY RESULTS, RESULTING DESIGNS, HARDWARE, SOFTWARE PRODUCTS OR ANY OTHER APPLICATIONS RESULTING FROM USE OF THE SUBJECT SOFTWARE.  FURTHER, GOVERNMENT AGENCY DISCLAIMS ALL WARRANTIES AND LIABILITIES REGARDING THIRD-PARTY SOFTWARE, IF PRESENT IN THE ORIGINAL SOFTWARE, AND DISTRIBUTES IT "AS IS."

Waiver and Indemnity:  RECIPIENT AGREES TO WAIVE ANY AND ALL CLAIMS AGAINST THE UNITED STATES GOVERNMENT, ITS CONTRACTORS AND SUBCONTRACTORS, AS WELL AS ANY PRIOR RECIPIENT.  IF RECIPIENT'S USE OF THE SUBJECT SOFTWARE RESULTS IN ANY LIABILITIES, DEMANDS, DAMAGES, EXPENSES OR LOSSES ARISING FROM SUCH USE, INCLUDING ANY DAMAGES FROM PRODUCTS BASED ON, OR RESULTING FROM, RECIPIENT'S USE OF THE SUBJECT SOFTWARE, RECIPIENT SHALL INDEMNIFY AND HOLD HARMLESS THE UNITED STATES GOVERNMENT, ITS CONTRACTORS AND SUBCONTRACTORS, AS WELL AS ANY PRIOR RECIPIENT, TO THE EXTENT PERMITTED BY LAW.  RECIPIENT'S SOLE REMEDY FOR ANY SUCH MATTER SHALL BE THE IMMEDIATE, UNILATERAL TERMINATION OF THIS AGREEMENT.