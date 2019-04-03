from ipykernel.kernelapp import IPKernelApp
from .kernel import ProActiveKernel
IPKernelApp.launch_instance(kernel_class=ProActiveKernel)