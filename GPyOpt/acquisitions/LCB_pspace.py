# Copyright (c) 2016, the GPyOpt Authors
# Licensed under the BSD 3-clause license (see LICENSE.txt)
import numpy as np


from .base import AcquisitionBase
from ..util.general import change_of_var_Phi,change_of_var_Phi_withGradients
from ..models import gpmodel

class AcquisitionLCB_pspace(AcquisitionBase):
    """
    GP-Lower Confidence Bound acquisition function

    :param model: GPyOpt class of model
    :param space: GPyOpt class of domain
    :param optimizer: optimizer of the acquisition. Should be a GPyOpt optimizer
    :param cost_withGradients: function
    :param jitter: positive value to make the acquisition more explorative

    .. Note:: does not allow to be used with cost

    """

    analytical_gradient_prediction = False ## Could be true but need to be tested

    def __init__(self, model, space, optimizer=None, cost_withGradients=None, exploration_weight=2, nb_output=1):
        self.optimizer = optimizer
        super(AcquisitionLCB_pspace, self).__init__(model, space, optimizer, nb_output=nb_output)
        self.exploration_weight = exploration_weight

        if cost_withGradients is not None:
            print('The set cost function is ignored! LCB acquisition does not make sense with cost.')  

    def _compute_acq(self, x):
        """
        Computes the GP-Lower Confidence Bound in p-space (rather than f-space, 
        in the case of non Gaussian likelihood)
        """
        m, s = self.model.predict(x)
        if type(self.model) == gpmodel.GPModelCustomLik:
            m, s = change_of_var_Phi(m, s)
    
        f_acqu = -m + self.exploration_weight * s
        return f_acqu


    def _compute_acq_withGradients(self, x):
        """
        Computes the GP-Lower Confidence Bound and its derivative
        """
        m, s, dmdx, dsdx = self.model.predict_withGradients(x) 

        if type(self.model) == gpmodel.GPModelCustomLik:
            m, v, dmdx, dvdx = change_of_var_Phi_withGradients(m, s, dmdx, dsdx)
            s = np.sqrt(v)
            dsdx = dvdx /(2 * s)

        f_acqu = -m + self.exploration_weight * s       
        df_acqu = -dmdx + self.exploration_weight * dsdx
        return f_acqu, df_acqu
    
     

    def _compute_acq_novar(self, x):
        """
        Computes the acquisition function without the uncertainty part i.e. the expected value of the fom
        """
        m, s = self.model.predict(x)
        if type(self.model) == gpmodel.GPModelCustomLik:
            m, _ = change_of_var_Phi(m, s)
    
        return m

    def _compute_acq_splitted(self, x):
        """
        Computes the two parts (expected value, std) used in the acqu function 
        """
        m, s = self.model.predict(x)
        if type(self.model) == gpmodel.GPModelCustomLik:
            m, s = change_of_var_Phi(m, s)
        return m, s