#!/usr/bin/env python3

import numpy as np
from scipy.interpolate import interp1d
from scipy.optimize import fsolve, newton, curve_fit
from scipy.special import binom

import matplotlib.pyplot as plt

vgn1_curve = np.loadtxt("VGN1@VGN20.csv", delimiter=',')
vgn2_curve = np.loadtxt("VGN2@VGN1_1.5.csv", delimiter=',')

idx = np.argsort(vgn1_curve[:,0])

vgn1_curve = vgn1_curve[idx]

vgn1 = interp1d(vgn1_curve[:,0], vgn1_curve[:,1], fill_value="extrapolate")

idx = np.argsort(vgn2_curve[:,0])

vgn2_curve = vgn2_curve[idx]

vgn2_curve[:,1] -= vgn1(1.5)

vgn2 = interp1d(vgn2_curve[:,0], vgn2_curve[:,1], fill_value="extrapolate")


x = np.linspace(0, 1.5, 100)

if False:
    plt.plot(x, vgn1(x))
    plt.plot(x, vgn2(x))
    
    plt.plot(x, vgn1(x) + vgn2(x)-vgn1(0))
    
    plt.xticks(np.arange(0, 1.51, 0.1))
    plt.yticks(np.arange(-10, 61, 5))
    
    plt.grid()
    
    plt.show()

def richards(t, A, B, K, Q):
    C = 1
    nu = 1
    return A + (K - A)/(C+Q*np.exp(-B*t))**(1/nu)

max_gain = vgn1(1.5) + vgn2(1.5) - vgn1(0)

@np.vectorize
def SN(t, N):
    t = t / 1.5

    if t < 0:
        return 0

    if t > 1:
        return max_gain

    retval = 0
    
    for n in range(N+1):
        retval += binom(-N-1, n) * binom(2 * N + 1, N - n) * t**(N + n + 1)

    print(retval)
        
    return retval * max_gain

def f(t, *args):
    retval = 0
    
    for i, c in enumerate(args):
        retval += c * t**(i+1)

    return retval

popt, pcov = curve_fit(f, x, vgn1(x) + vgn2(x)-vgn1(0), [
    6.73992332,
    -148.29699193,
    992.3236711,
    -1175.36635491,
    -1369.00052319,
    4652.37169521,
    -4608.26945438,
    2049.95556908,
    -348.93151547
])

plt.plot(x, vgn1(x) + vgn2(x)-vgn1(0))
plt.plot(x, f(x, *popt))

print(popt)
#print(pcov)
print(np.linalg.cond(pcov))

@np.vectorize
def getr(xp):
    r = np.roots(np.flip(np.concatenate(([-xp], popt))))

    r = np.real(r[np.isreal(r) & (r >= 0) & (r < 1.5)])[0]
    
    return r

x = np.arange(0, 60.5, 0.5)

print(x)
print(np.round(getr(x), decimals=3))

with open("gain_lookup.csv", "w") as f:
    for x, y in  zip(x, np.round(getr(x), decimals=3)):
        f.write(f"{x},{y:.3f}\n")
    
plt.figure()
plt.plot(x, getr(x))

y = np.arange(0, 1.5, 0.1)

plt.plot(vgn1(y)+vgn2(y)-vgn1(0), y)

plt.show()
    
