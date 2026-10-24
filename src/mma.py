"""Method of moving asymptotes (Svanberg 1987; the 2007 'MMA and GCMMA' note), dense subproblem.

Problem form (Svanberg's standard form):
    min  f0(x) + a0 z + sum_i (c_i y_i + 0.5 d_i y_i^2)
    s.t. f_i(x) - a_i z - y_i <= 0,  i = 1..m;   xmin <= x <= xmax;  y >= 0;  z >= 0.
With f0 = 0, a0 = 1, a_i = 1 for a set of functions and large c_i, the problem is the bound
(epigraph) form of  min_x max_i f_i(x).  `mmasub` returns the next iterate and the multipliers of the
subproblem; `subsolv` is the primal-dual interior-point solver of the convex subproblem. The number of
constraints m is small here (at most a few tens), so the reduced m x m system is formed densely.
"""
from __future__ import annotations

import numpy as np


def mmasub(m, n, it, xval, xmin, xmax, xold1, xold2, df0dx, fval, dfdx, low, upp, a0, a, c, d, move=0.5,
           asyinit=0.5, asyincr=1.2, asydecr=0.7):
    albefa, raa0, epsimin = 0.1, 1e-5, 1e-7
    span = xmax - xmin
    if it <= 2:
        low = xval - asyinit * span
        upp = xval + asyinit * span
    else:
        zzz = (xval - xold1) * (xold1 - xold2)
        factor = np.ones(n)
        factor[zzz > 0] = asyincr
        factor[zzz < 0] = asydecr
        low = xval - factor * (xold1 - low)
        upp = xval + factor * (upp - xold1)
        low = np.clip(low, xval - 10 * span, xval - 0.01 * span)
        upp = np.clip(upp, xval + 0.01 * span, xval + 10 * span)
    alfa = np.maximum.reduce([low + albefa * (xval - low), xval - move * span, xmin])
    beta = np.minimum.reduce([upp - albefa * (upp - xval), xval + move * span, xmax])
    xmami = np.maximum(span, 1e-5)
    ux1, xl1 = upp - xval, xval - low
    ux2, xl2 = ux1 * ux1, xl1 * xl1
    p0 = np.maximum(df0dx, 0.0)
    q0 = np.maximum(-df0dx, 0.0)
    pq0 = 0.001 * (p0 + q0) + raa0 / xmami
    p0 = (p0 + pq0) * ux2
    q0 = (q0 + pq0) * xl2
    P = np.maximum(dfdx, 0.0)
    Q = np.maximum(-dfdx, 0.0)
    PQ = 0.001 * (P + Q) + raa0 / xmami[None, :]
    P = (P + PQ) * ux2[None, :]
    Q = (Q + PQ) * xl2[None, :]
    b = P @ (1.0 / ux1) + Q @ (1.0 / xl1) - fval
    sol = subsolv(m, n, epsimin, low, upp, alfa, beta, p0, q0, P, Q, a0, a, b, c, d)
    return sol, low, upp


def subsolv(m, n, epsimin, low, upp, alfa, beta, p0, q0, P, Q, a0, a, b, c, d):
    een, eem = np.ones(n), np.ones(m)
    epsi = 1.0
    x = 0.5 * (alfa + beta)
    y, z, lam = eem.copy(), 1.0, eem.copy()
    xsi = np.maximum(een / (x - alfa), een)
    eta = np.maximum(een / (beta - x), een)
    mu = np.maximum(eem, 0.5 * c)
    zet, s = 1.0, eem.copy()

    def residual(x, y, z, lam, xsi, eta, mu, zet, s, epsi):
        ux1, xl1 = upp - x, x - low
        plam = p0 + P.T @ lam
        qlam = q0 + Q.T @ lam
        gvec = P @ (1.0 / ux1) + Q @ (1.0 / xl1)
        dpsidx = plam / ux1 ** 2 - qlam / xl1 ** 2
        r = np.concatenate([dpsidx - xsi + eta, c + d * y - mu - lam, [a0 - zet - a @ lam],
                            gvec - a * z - y + s - b, xsi * (x - alfa) - epsi, eta * (beta - x) - epsi,
                            mu * y - epsi, [zet * z - epsi], lam * s - epsi])
        return np.sqrt(r @ r), np.max(np.abs(r))

    while epsi > epsimin:
        rnorm, rmax = residual(x, y, z, lam, xsi, eta, mu, zet, s, epsi)
        ittt = 0
        while rmax > 0.9 * epsi and ittt < 200:
            ittt += 1
            ux1, xl1 = upp - x, x - low
            ux2, xl2 = ux1 * ux1, xl1 * xl1
            ux3, xl3 = ux1 * ux2, xl1 * xl2
            plam = p0 + P.T @ lam
            qlam = q0 + Q.T @ lam
            gvec = P @ (1.0 / ux1) + Q @ (1.0 / xl1)
            GG = P / ux2[None, :] - Q / xl2[None, :]
            dpsidx = plam / ux2 - qlam / xl2
            delx = dpsidx - epsi / (x - alfa) + epsi / (beta - x)
            dely = c + d * y - lam - epsi / y
            delz = a0 - a @ lam - epsi / z
            dellam = gvec - a * z - y - b + epsi / lam
            diagx = 2 * (plam / ux3 + qlam / xl3) + xsi / (x - alfa) + eta / (beta - x)
            diagxinv = 1.0 / diagx
            diagy = d + mu / y
            diaglamyi = s / lam + 1.0 / diagy
            blam = dellam + dely / diagy - GG @ (delx * diagxinv)
            Alam = np.diag(diaglamyi) + (GG * diagxinv[None, :]) @ GG.T
            AA = np.zeros((m + 1, m + 1))
            AA[:m, :m] = Alam
            AA[:m, m] = a
            AA[m, :m] = a
            AA[m, m] = -zet / z
            sol = np.linalg.solve(AA, np.concatenate([blam, [delz]]))
            dlam, dz = sol[:m], sol[m]
            dx = -delx * diagxinv - (GG.T @ dlam) * diagxinv
            dy = -dely / diagy + dlam / diagy
            dxsi = -xsi + epsi / (x - alfa) - (xsi * dx) / (x - alfa)
            deta = -eta + epsi / (beta - x) + (eta * dx) / (beta - x)
            dmu = -mu + epsi / y - (mu * dy) / y
            dzet = -zet + epsi / z - zet * dz / z
            ds = -s + epsi / lam - (s * dlam) / lam
            xx = np.concatenate([y, [z], lam, xsi, eta, mu, [zet], s])
            dxx = np.concatenate([dy, [dz], dlam, dxsi, deta, dmu, [dzet], ds])
            stmxx = np.max(-1.01 * dxx / xx)
            stmalfa = np.max(-1.01 * dx / (x - alfa))
            stmbeta = np.max(1.01 * dx / (beta - x))
            steg = 1.0 / max(stmalfa, stmbeta, stmxx, 1.0)
            old = (x, y, z, lam, xsi, eta, mu, zet, s)
            itto, rnew = 0, 2 * rnorm
            while rnew > rnorm and itto < 50:
                itto += 1
                x = old[0] + steg * dx
                y = old[1] + steg * dy
                z = old[2] + steg * dz
                lam = old[3] + steg * dlam
                xsi = old[4] + steg * dxsi
                eta = old[5] + steg * deta
                mu = old[6] + steg * dmu
                zet = old[7] + steg * dzet
                s = old[8] + steg * ds
                rnew, rmax = residual(x, y, z, lam, xsi, eta, mu, zet, s, epsi)
                steg /= 2
            rnorm = rnew
        epsi *= 0.1
    return dict(x=x, y=y, z=z, lam=lam, xsi=xsi, eta=eta, mu=mu, zet=zet, s=s)
