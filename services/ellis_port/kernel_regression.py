import numpy as np
import scipy as sp

from .cross_validation import cv_score
from .univariate_predictor import UnivariatePredictor
from .interpolation_splits import InterpolationSplits

class KernelRegression(UnivariatePredictor):
    """
    Kernel regression model for univariate data, supports polynomial feature mapping.
    """
    def __init__(self, bw=None, degree=1, tol=np.finfo(np.float64).eps):
        self.bw = bw
        self.degree = degree
        self.tol = tol

    def _fmap(self, x):
        """
        Maps input x to polynomial features of the given degree.

        Parameters:
        x (np.ndarray): Input feature array.

        Returns:
        np.ndarray: Feature mapped array.
        """
        return np.vstack([x ** i for i in range(self.degree + 1)]).T

    def _predict_single(self, X, y, x, w):
        """
        Predicts output using the kernel regression model.

        Parameters:
        x (np.ndarray): Input feature array.

        Returns:
        np.ndarray: Predicted values.
        """
        XTW = X.T * w
        matrix_x = np.dot(XTW, X) + self.tol * np.eye(X.shape[1])
        matrix_b = np.dot(XTW, y)

        try:
            c = np.linalg.solve(matrix_x, matrix_b)
        except:
            print("Could not compute solution, so either matrix_x is singular or not square.")
            print("Will try now with the pseudo-inverse of matrix_x...")
            c = np.linalg.pinv(matrix_x).dot(matrix_b)
            print("Success with pseudo-inverse of matrix_x!")

        ypred = np.dot(x, c)
        return ypred

    def __predict(self, X, y, Xpred, W):
        n, d = Xpred.shape
        ypred = np.zeros(n)
        for i in range(n):
            ypred[i] = self._predict_single(X, y, Xpred[i], W[i])
        return ypred

    def _fit(self, x, y):
        x, y = x.flatten(), y.flatten()
        if self.bw is None:
            models = [KernelRegression(bw=bw) for bw in np.linspace(1, 100, 100)]
            scores = cv_score(models, InterpolationSplits(x, y))
            scores = np.mean(scores, axis=1)
            idx = np.argmin(scores)
            self._bw = models[idx].bw
        else:
            self._bw = self.bw

        self.x = x
        self.y = y
        return self

    def _predict(self, xs):
        xs = xs.flatten()

        xs = np.atleast_1d(xs)
        x, y, h = self.x, self.y, self._bw

        D = sp.spatial.distance.cdist(np.atleast_2d(xs).T, np.atleast_2d(x).T, metric='sqeuclidean')
        W = np.exp(-D / (2 * h ** 2))

        X = self._fmap(x)
        X0 = self._fmap(xs)

        ypred = self.__predict(X, y, X0, W)
        return ypred
