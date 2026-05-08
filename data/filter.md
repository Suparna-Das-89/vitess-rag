# VITESS Module Filter

There are two filter modules. Both select trajectories with certain parameter values. It is a numerical operation that does not have an equivalent in reality (though some instrument components have a similar task). Only trajectories with values of the chosen parameters within the given ranges are considered further. 

In **filter** , up to 4 parameter can be chosen and combined logically with AND, OR or the combination: (par1 AND par2) OR (par3 AND par4) for sufficient flexibility.

In contrast, **filter2D** only allows a limitation of the spatial or divergence distribution of the beam, but the beam intensity can be varied in 2D over the given range. The distribution of the transmission is defined by a matrix read by the module. It assumes equal spacing in both dimensions over the given range. The intensity of a trajectory is multiplied by the factor found in the matrix for its 2D position or divergence resp.

## The following table lists the parameters of the module 'filter'.




| Parameter Unit   | Description                                                             | Range or Values                                                                  | Command Option   |
|---------------------------|------------------------------------------------------------------------------|--------------------------------------------------------------------------------------|----------------------|
| filter combination        | logical connection of the different filters                                  | AND, OR, AND_OR_AND                                                                  | -C                   |
| filter parameter 1        | 1st parameter determining which trajectories are kept                        | none, pos_y, pos_z, div_y, div_z, lambda, energy, time, k_y, k_z, r, phi, col_vert, col_hor, color | -I                   |
| filter 1 min value        | minimal value of parameter 1, required for the trajectory to pass the filter |                           —                                                           | -u                   |
| filter 1 max value        | maximal value of parameter 1, required for the trajectory to pass the filter |                                             —                                         | -U                   |
| filter parameter 2        | 2nd parameter determining which trajectories are kept                        | none, pos_y, pos_z, div_y, div_z, lambda, energy, time, k_y, k_z, r, phi, col_vert, col_hor, color | -J                   |
| filter 2 min value        | minimal value of parameter 2, required for the trajectory to pass the filter |                            —                                                          | -v                   |
| filter 2 max value        | maximal value of parameter 2, required for the trajectory to pass the filter |                            —                                                          | -V                   |
| filter parameter 3        | 3rd parameter determining which trajectories are kept                        | none, pos_y, pos_z, div_y, div_z, lambda, energy, time, k_y, k_z, r, phi, col_vert, col_hor, color | -K                   |
| filter 3 min value        | minimal value of parameter 3, required for the trajectory to pass the filter |                                 —                                                     | -w                   |
| filter 3 max value        | maximal value of parameter 3, required for the trajectory to pass the filter |                                  —                                                    | -W                   |
| filter parameter 4        | 4th parameter determining which trajectories are kept                        | none, pos_y, pos_z, div_y, div_z, lambda, energy, time, k_y, k_z, r, phi, col_vert, col_hor, color | -L                   |
| filter 4 min value        | minimal value of parameter 4, required for the trajectory to pass the filter |                                 —                                                     | -x                   |
| filter 4 max value        | maximal value of parameter 4, required for the trajectory to pass the filter |                                —                                                      | -X                   |


## The following table lists the parameters of the module 'filter2D'.

| Parameter  Unit   | Description                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                                           | Range or Values     | Command Option   |
|---------------------------|-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|-------------------------|----------------------|
| filter parameter          | Here it is defined as a function of which parameter the intensity is altered                                                                                                                                                                                                                                                                                                                                                                                                                                                              | "position", "divergence" | -P                   |
| filter table              | Name of the file containing the filter matrix. The filter range is divided into a number of channels corresponding to the number of columns  *N* _ *col*  and rows  *N* _ *row*  in the matrix.  The total width is divided into  *N* _ *col*  channels of constant width. The total height is divided into  *N* _ *row*  channels of constant height.  For each of the  *N* _ *col*  x  *N* _ *row*  elements, a factor has to be given in the matrix, by which the intensity of a trajectory (with this position or divergence) is multiplied | —                 | -F                   |
| min. y  [cm]             | lower bound of the filter range in horizontal direction (width)                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |  —  | -y                   |
| max. y  [cm]             | upper bound of the filter range in horizontal direction (width)                                                                                                                                                                                                                                                                                                                                                                                                                                                                           |              —           | -Y                   |
| min. z  [cm]             | lower bound of the filter range in vertical direction (height)                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |          —               | -z                   |
| max. z  [cm]             | upper bound of the filter range in vertical direction (height)                                                                                                                                                                                                                                                                                                                                                                                                                                                                            |            —             | -Z                   |

### Example of filter table file.

This example demonstrates a filter table with a matrix of 11 rows by 11 columns, as shown in the “Filter matrix example: 11x11 binary matrix with central 3x3 zero block” section. In this matrix, the central 3x3 region is assigned a probability value of 0, representing the absorption of neutron trajectories. The rest of the matrix has a value of 1, allowing trajectories to pass through while keeping the original probability. Any number different from 1 would change the original probability. 

When used in 'position' mode, this filter creates an absorbing mask at the center of the defined y and z range. The values in the matrix can be any real number, but in this example, 0 and 1 are chosen to illustrate the creation of an absorbing region. The range of y and z, as specified in the input parameters, determines the size of each bin in the matrix. The number of bins in the y and z directions corresponds to the rows and columns defined in the filter table file. This example ensures that the filter accurately applies to the defined spatial region based on the provided configuration. 


#### Filter matrix example: 11x11 binary matrix with central 3x3 zero block

$
\begin{bmatrix}
1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 \\
1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 \\
1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 \\
1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 \\
1 & 1 & 1 & 1 & 0 & 0 & 0 & 1 & 1 & 1 & 1 \\
1 & 1 & 1 & 1 & 0 & 0 & 0 & 1 & 1 & 1 & 1 \\
1 & 1 & 1 & 1 & 0 & 0 & 0 & 1 & 1 & 1 & 1 \\
1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 \\
1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 \\
1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 \\
1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1 & 1
\end{bmatrix}
$

