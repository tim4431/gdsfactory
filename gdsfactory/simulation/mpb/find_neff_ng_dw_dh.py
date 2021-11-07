"""Compute group and effective index for different waveguide widths and heights.

Reproduce Yufei thesis results with MPB.

https://www.photonics.intec.ugent.be/contact/people.asp?ID=332
"""

import pathlib

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.interpolate import interp2d

from gdsfactory.config import PATH
from gdsfactory.simulation.mpb.find_modes_dispersion import find_modes_dispersion
from gdsfactory.simulation.mpb.find_neff import find_neff

PATH.modes = pathlib.Path.cwd() / "data"

w0 = 0.465
h0 = 0.215

dwmax = 10e-3
dhmax = 5e-3


def find_neff_ng_dw_dh(
    ncore: float = 3.47668,
    nclad: float = 1.44401,
    dwmax: float = 30e-3,
    dhmax: float = 20e-3,
    w0: float = w0,
    h0: float = h0,
    wavelength: float = 1.55,
    steps: int = 11,
    with_dispersion: bool = True,
) -> pd.DataFrame:
    """Computes group and effective index for different widths and heights."""
    dw = np.linspace(-dwmax, dwmax, steps)
    dh = np.linspace(-dhmax, dhmax, steps)

    neffs = []
    ngs = []
    dhs = []
    dws = []

    for dwi in dw:
        for dhi in dh:
            if with_dispersion:
                r = find_modes_dispersion(
                    wg_width=w0 + dwi, wg_thickness=h0 + dhi, wavelength=wavelength
                )
            else:
                r = find_neff(
                    wg_width=w0 + dwi, wg_thickness=h0 + dhi, wavelength=wavelength
                )

            neffs.append(r["neff"])
            ngs.append(r["ng"])
            dws.append(dwi)
            dhs.append(dhi)

    df = pd.DataFrame(dict(dw=dws, dh=dhs, neff=neffs, ng=ngs))
    return df


def plot_neff_ng_dw_dh(
    w0: float = w0,
    h0: float = h0,
    wavelength: float = 1.55,
    with_dispersion: bool = True,
) -> None:

    if with_dispersion:
        filepath = pathlib.Path(PATH.modes / "mpb_dw_dh_dispersion.csv")
        r = find_modes_dispersion(wg_width=w0, wg_thickness=h0, wavelength=wavelength)
        neff0 = r["neff"]
        ng0 = r["ng"]
    else:
        filepath = pathlib.Path(PATH.modes / "mpb_dw_dh.csv")
        r = find_neff(wg_width=w0, wg_thickness=h0, wavelength=wavelength)
        neff0 = r["neff"]
        ng0 = r["ng"]

    if filepath.exists():
        df = pd.read_csv(filepath)
    else:
        df = find_neff_ng_dw_dh(wavelength=wavelength)
        df.to_csv(filepath)

    dws = df.dw.values
    dhs = df.dh.values
    ngs = df.ng.values
    neffs = df.neff.values

    # neff interpolation
    f_w = interp2d(neffs, ngs, np.array(dws), kind="cubic")
    f_h = interp2d(neffs, ngs, np.array(dhs), kind="cubic")

    ws = w0 + np.array(dws)
    hs = h0 + np.array(dhs)

    plt.plot(ws * 1e3, hs * 1e3, "ko")
    extracted_dw = []
    extracted_dh = []

    for neff, ng in zip(neffs, ngs):
        temp_w = f_w(neff, ng) + w0
        temp_h = f_h(neff, ng) + h0
        extracted_dw.append(temp_w * 1e3)
        extracted_dh.append(temp_h * 1e3)

    plt.plot(extracted_dw, extracted_dh, "rx")
    plt.xlabel("width (nm)")
    plt.ylabel("height (nm)")

    plt.figure()
    plt.plot(neffs, ngs, "ro")
    plt.plot(neff0, ng0, "bx")
    plt.xlabel("neff")
    plt.ylabel("ng")
    plt.show()


if __name__ == "__main__":
    plot_neff_ng_dw_dh()