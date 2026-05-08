# VITESS Module Writeout

The module writeout can be inserted between two other VITESS modules or put to the end of the instrument. It records the output of the preceding module by writing data sets of trajectories (or 'neutrons' or 'events') into an ASCII or binary file. The data can be written in 5 different formats: VITESS, McStas, MCPL, MCNP and MCNPX. For ASCII output, the separator (space or tab) and the data format (float or exponential) has to be specified. It is possible to write all data sets, but there are also different options to select the trajectories that are written to this file (see table [Parameters for Module 'writeout'](#the-following-table-lists-the-parameters-of-the-module-writeout)). In any case, all trajectories are written unchanged to the pipe for the following module, so the simulation is not disturbed by using this  module. 

There is the possibility to disable the module, i.e. suppress writing the output. For VITESS, there is also the option to select the written parameters (see table [Parameters for Module 'writeout'](#the-following-table-lists-the-parameters-of-the-module-writeout)). Note that the output file needs something like 0.1 kByte per trajectory and may therefore become very large.

The module read_in can read the data of the *output file* or data sets written by writeout or a corresponding module in another simulation program. see the [read_in documentation](https://vitess.iffgit.fz-juelich.de/vitess/read_in.html) for more information on how to use the read_in module .

To read and write data in MCPL format, the utiliy mcpl by Thomas Kittelmann is used (see [MCPL-Homepage](https://mctools.github.io/mcpl/) ) which stores the trajectories in binary format. The interface does not allow options like using several input files, ASCII format, etc.

The following information is written for each trajectory (or neutron) in VITESS format:

## Table: VITESS Neutron Trajectory Data Format: Columns, Units, Coordinates, Direction, and Spin Parameters:

| Column | Description                                         | Unit | Notes                                                                             |
| ------ | --------------------------------------------------- | ---- | --------------------------------------------------------------------------------- |
| 1      | ID of the trajectory                                | —    | e.g. `AA000123456`                                                                |
| 2      | Tracing information                                 | —    | `T` = tracing, `N` = no tracing                                                   |
| 3      | Color of the trajectory                             | —    | reserved for user's demands                                                       |
| 4      | Time of flight                                      | ms   | —                                                                                 |
| 5      | Neutron wavelength                                  | Å    | —                                                                                 |
| 6      | Intensity (or weight) represented by the trajectory | n/s  | —                                                                                 |
| 7      | x-coordinate of the position                        | cm   | with respect to the coordinate system provided by the module preceding [`writeout`](https://vitess.iffgit.fz-juelich.de/vitess/writeout.html) |
| 8      | y-coordinate of the position                        | cm   | with respect to the coordinate system provided by the module preceding [`writeout`](https://vitess.iffgit.fz-juelich.de/vitess/writeout.html) |
| 9      | z-coordinate of the position                        | cm   | with respect to the coordinate system provided by the module preceding [`writeout`](https://vitess.iffgit.fz-juelich.de/vitess/writeout.html) |
| 10     | x-coordinate of the flight direction                | —    | direction cosine                                                                  |
| 11     | y-coordinate of the flight direction                | —    | direction cosine                                                                  |
| 12     | z-coordinate of the flight direction                | —    | direction cosine                                                                  |
| 13     | x-coordinate of the spin                            | —    | —                                                                                 |
| 14     | y-coordinate of the spin                            | —    | —                                                                                 |
| 15     | z-coordinate of the spin                            | —    | —                                                                                 |




## The following table lists the parameters of the module 'writeout':

| Parameter  Unit           | Description                                                                                                                                                                     | Range or Values                         | Command Option   |
|-----------------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|---------------------------------------------|----------------------|
| ASCII output file                 | Name of the output file containing the neutron trajectories                                                                                                                         | —                                            | -A                   |
| Active?                           | "no": no output is written  <br>"yes": output file is written                                                                                                                           | "no"  <br>"yes"                                 | -a                   |
| Header                            | "no": no header is written  <br>"yes": first 2 or 3 lines contain information, mainly about the content of the columns                                                                  | "no"  <br>"yes"                                 | -a                   |
| data format                       | The format in which the output file will be written                                                                                                                                 | "VITESS"  <br>"McStas"  <br>"MCPL"  <br>"MCNP"  <br>"MCNPX" | -f                   |
| storage format                    | Data format in which float numbers are written to the output file  <br>"exp": exponential (scientific) representation,  <br>"float": floating point representation, <br>"binary": binary format | "exp"  <br>"float"  <br>"binary"                    | -F                   |
| separator                         | Character used to separate the numbers in a VITESS output file  MCNPX and McStas data are separated by 'space'                                                                      | "Space"  <br>"Tabulator"                        | -S                   |
| Intensity factor for MCNPX  [n/s] | The weight of each neutron trajectory  is divided by this factor to yield the counts in the MCNPX simulation.  The factor is: $F = I_{src}  / N _{MCNPX-Events}$                        | > 0  <br>typical 1.0e8  <br>default: 1.0          | -I                   |
| Columns                           | Choice of output parameters for VITESS format                                                                                                                                       | —                                           | -c                   |
| writeout color                    | (optional) Only trajectories of the given color are written to the output file.  <br>Color -1 means: all trajectories are written                                                       | ≥ -1 (int)  default: -1                 | -C                   |
| filter lambda min/max  [Å]        | (optional) Only neutrons within the given wavelength range are read                                                                                                                 | >0                                          | -l  <br>-L               |
| filter Y pos. min/max  [cm]       | (optional) Only neutrons within the given horizontal space range are read                                                                                                           | any                                         | -y  <br>-Y               |
| filter Z pos. min/max  [cm]       | (optional) Only neutrons within the given vertical space range are read                                                                                                             | any                                         | -z  <br>-Z               |
| filter hor. div. min/max  []      | (optional) Only neutrons within the given horizontal divergence range are read                                                                                                      | any                                         | -e  <br>-d               |
| filter vert. div. min/max  []     | (optional) Only neutrons within the given vertical divergence range are read                                                                                                        | any                                         | -E  <br>-D               |
| filter div. min/max  []           | (optional) Only neutrons within the given total divergence range are read                                                                                                           | ≥ 0                                         | -g  <br>-G               |

