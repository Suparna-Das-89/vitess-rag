# VITESS Module Capture Flux

The module **capture_flux** (folder 'evaluate') calculates the capture flux (at any point of the instrument). The capture flux method is used to determine absolute flux values in a beam line. A gold foil is introduced for some hours and the activation of the gold is measured. As the absorption probability of neutrons rises linearly with wavelength, one does not get the real flux but the integral

$$
\Phi_{\mathrm{capture}} = \int \phi(\lambda)\,\frac{\lambda}{\lambda_{\mathrm{ref}}}\,d\lambda
$$

(The reference wavelength is usually 1.798 Å.) This integral is calculated in the module thus allowing a direct comparison with measurements. Reference wavelength, shape and size of the foil need to be given. Additionally, the wavelength range contributing to the capture flux can be limited.

## The following table lists the parameters of the module 'capture_flux':

| Parameter  Unit | Description | Range or Values | Command Option |
|---|---|---|---|
| reference wavelength  [Å] | reference wavelength in the capture flux definition, usually 1.798 Å (cf. text). <br>If 0.0 is given, no reference wavelength is used | ≥ 0 | -R |
| window type | shape of the gold foil <br>0 (no restriction): every neutron is counted and the area is taken as 1 cm² | 0: no restriction <br>1: circular <br>2: rectangular | -t |
| radius  [cm] | for circular foil: radius of the foil | > 0 | -r |
| center y<br>center z  [cm] | for circular foil: center y (horizontal) and z (vertical) of the foil | any | -y <br>-z |
| min. y<br>max. y  [cm] | for rectangular foil: minimal (right) and maximal (left) y value of the foil | any | -w <br>-W |
| min. z<br>max. z  [cm] | for rectangular foil: minimal (bottom) and maximal (top) z value of the foil | any | -h <br>-H |
| min. lambda<br>max. lambda  [Å] | minimal and maximal wavelength that is considered for the integration <br>If minimal and maximal wavelength are zero this option is ignored | > 0 <br>λ_min < λ_max | -l <br>-L |
