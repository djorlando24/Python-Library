'''Module to compute the signal trapping corrections for the Taitech 2014-2
data.

Strategy:
1.  Use the calibrated amounts of liquid and gas to partition radiography into
gas absorption and liquid absorption.
2.  Scale gas and liquid to the fluorescence line energies.
3.  Fit an axisymmetric distribution to the radiography at the fluorescence line energy.
4.  Model the signal trapping
5.  Correct the fluorescence data, writing a new hdf5 dataset.

Alan Kastengren, XSD, APS

Started: October 26, 2014
'''
import matplotlib.pyplot as plt
import h5py
import numpy as np
import Signal_Trapping_Fitted as stf
import Projection_Fit as pf
from scipy import optimize
from scipy import interpolate
import ALK_Utilities as ALK

def fcompute_component_radiography(hdf_file,dataset_name,abs_coeff):
    '''Computes the absorption from a component.
    Variables:
    hdf_file: h5py File object for file we are examining.
    dataset_name: name of dataset with calibrated component data
    abs_coeff: absorption coefficient of the component at the desired energy.
    Returns: absorption array in extinction lengths
    '''
    return abs_coeff*hdf_file[dataset_name][...]

def fscale_absorption(absorption_data,abs_coeff_ratio):
    '''Computes the absorption data scaled to the correct energy.
    Variables:
    absorption_data: array or list with absorption data at current energy.
    abs_coeff_ratio: abs_coeff at desired energy / abs_coeff at current energy.
    Returns: scaled absorption in terms of extinction lengths
    '''
    return absorption_data * abs_coeff_ratio

def ffit_distribution(proj_fit_function,x,projection_data,parameter_guesses):
    '''Computes the axisymmetric fit to a distribution
    Variables:
    projection_data: data for the projection
    proj_fit_function: function to be used to fit the projection
    x: x values for projection_data points
    parameter_guesses: guesses for proj_fit_function parameters
    Returns: fitted parameters
    '''
    fit_parameters,covariance = optimize.curve_fit(proj_fit_function,x,projection_data,parameter_guesses)
    print fit_parameters
    print covariance
    return fit_parameters

def fcompute_signal_trapping(x_lims, z_lims, num_x, num_z, rad_fit_function, rad_fit_args, 
                             fluor_fit_function, fluor_fit_args, x_center_rad, x_center_fluor, detector_negative=True):
    '''Computes the signal trapping given a fit to the distribution of absorption.
    Variables:
    x_lims, z_lims, num_x, num_z: size and shape of arrays for computations
    rad_fit_function: function used to fit absorption, in terms of extinction lengths
    rad_fit_args: arguments for rad_fit_function to give correct distribution
    fluor_fit_function: function used to fit fluorescence
    fluor_fit_args: arguments for fluor_fit_function to give correct distribution
    x_center_(rad,fluor): x value where the axisymmetric distribution is centered
    detector_negative: if True, detector is on -x side of the experiment.
    Returns:
    x_vals: x values for the array, since it won't necessarily correspond to original data points.
    trap: transmission of fluorescence through sample for each x.
    '''
    x,trap,dummy = stf.fcompute_signal_trapping(x_lims, z_lims, num_x, num_z, rad_fit_function, 
                                                rad_fit_args, fluor_fit_function, fluor_fit_args, 
                                                x_center_rad, x_center_fluor, detector_negative)
    return x,trap

def fwrite_corrected_fluorescence(hdf_file,x_dataset_name,old_dataset_name,new_dataset_name,sig_trap_x,sig_trap_trans):
    '''Corrects for signal trapping and writes to file.
    Variables:
    hdf_file: h5py File object for file we are examining.
    x_dataset_name: dataset with x values for the data
    old_dataset_name: name of dataset with data before signal trapping correction
    new_dataset_name: name for corrected dataset
    sig_trap_x: x values for signal trapping array
    sig_trap_trans: amount of signal trapping
    Returns: None
    '''
    #Interpolate the sig_trap array to the actual x points where the data are taken.
    fluor_trans = interpolate.interp1d(sig_trap_x,sig_trap_trans)(hdf_file[x_dataset_name][...])
    ALK.fwrite_HDF_dataset(hdf_file, new_dataset_name, hdf_file[old_dataset_name][...]/fluor_trans)
    ALK.fwrite_HDF_dataset(hdf_file,old_dataset_name+'SignalTrappingTransmission',fluor_trans)
    return