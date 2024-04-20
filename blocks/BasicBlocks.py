# -*- coding:utf-8 -*-

"""
University of Sherbrooke
Date:
Authors: Mamadou Mountagha BAH & Pierre-Marc Jodoin
License:
Other: Suggestions are welcome
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

class ResidualBlock(nn.Module):
    """
    this block is the building block of the residual network. it takes an 
    input with in_channels, applies some blocks of convolutional layers
    to reduce it to out_channels and sum it up to the original input,
    """
    
    #Version ReLu-only pre-activation

    def __init__(self, in_channels,out_channels, depth_wise=True, bottleneck=False):
        super(ResidualBlock, self).__init__()
        midle_channels =  in_channels + out_channels 
        if midle_channels % 2 == 0:
            midle_channels = midle_channels // 2
        else:
            midle_channels = midle_channels // 2 + 1
            
        current = in_channels
        
        conv_layers = nn.ModuleList()
        
        if bottleneck:
            conv_layers.append(nn.Conv2d(in_channels=in_channels, out_channels=midle_channels, kernel_size=1, stride=1, padding=0))
            conv_layers.append(nn.BatchNorm2d(midle_channels))
            conv_layers.append(nn.ReLu())
            current = midle_channels
        
        if depthwise :
            conv_layers.append(nn.Conv2d(in_channels=current, out_channels=current, kernel_size=3, stride=1, padding=1, groups=current))
            conv_layers.append(nn.Conv2d(in_channels=current, out_channels=out_channels, kernel_size=1, stride=1, padding=0))
        else:
            conv_layers.append(nn.Conv2d(in_channels=current, out_channels=out_channels, kernel_size=3, stride=1, padding=1))
        
        conv_layers.append(nn.BatchNorm2d(out_channels))    
        conv_layers.append(nn.ReLu())
        conv_layers.append(nn.Conv2d(in_channels=out_channels, out_channels=out_channels, kernel_size=1, stride=1, padding=0))
        conv_layers.append(nn.BatchNorm2d(out_channels))
        self.mainbranch = nn.Sequential(*conv_layers)
        self.skip = nn.Sequential()
        if in_channels != out_channels :
            self.skip = nn.Conv2d(in_channels=in_channels, out_channels=out_channels, kernel_size=1, stride=1, padding=0)
        
    def forward(self, x):
        output = self.mainbranch(x)
        output += self.skip(x)
        
        return F.relu(output)
        
        


class DenseBlock(nn.Module):
    """
    This block is the building block of the Dense network. It takes an
    input with in_channels, applies some blocks of convolutional, batchnorm layers
    and then concatenate the output with the original input
    """
    #Dense block with 3 layers (bn-relu-conv1-conv2)
    def __init__(self, in_channels, depth_wise=True, bottleneck=False):
        super(DenseBlock, self).__init__()
        midle_channels =  in_channels 
        if in_channels % 2 == 0:
            midle_channels = midle_channels // 2
        else:
            midle_channels = midle_channels // 2 + 1
            
        current = in_channels
        
        conv_layers = nn.ModuleList()
        
        if bottleneck:
            conv_layers.append(nn.Conv2d(in_channels=in_channels, out_channels=midle_channels, kernel_size=1, stride=1, padding=0))
            conv_layers.append(nn.BatchNorm2d(midle_channels))
            conv_layers.append(nn.ReLu())
            current = midle_channels
        
        if depthwise :
            conv_layers.append(nn.Conv2d(in_channels=current, out_channels=current, kernel_size=3, stride=1, padding=1, groups=current))
            conv_layers.append(nn.Conv2d(in_channels=current, out_channels=in_channels, kernel_size=1, stride=1, padding=0))
        else:
            conv_layers.append(nn.Conv2d(in_channels=current, out_channels=in_channels, kernel_size=3, stride=1, padding=1))
        
        conv_layers.append(nn.BatchNorm2d(out_channels))    
        conv_layers.append(nn.ReLu())
        self.dense = nn.Sequential(*conv_layers)
        self.regularise = nn.Sequential(
            nn.Conv2d(in_channels=in_channels*2, out_channels=in_channels*2, kernel_size=1, stride=1, padding=0),
            nn.BatchNorm2d(nn.BatchNorm2d(out_channels)*2),
            nn.ReLu()
            )
        
    def forward(self, x):
            
        output = self.dense(x)
        output = torch.cat((x, output), 1)
        output = self.regularise(output)
           
        return output


class ConvBottleneck(nn.Module):
    """
    This block takes an input with in_channels reduces number of channels by a certain
    parameter "downsample" through kernels of size 1x1, 3x3, 1x1 respectively.
    """

    def __init__(self,in_channels,downsample, depth_wise=False):
        super(BottleneckBlock, self).__init__()
        conv_layers = nn.ModuleList()
        median_channels = in_channels // downsample
        
        conv_layers.append(nn.Conv2d(in_channels=in_channels, out_channels=median_channels, kernel_size=1, stride=1, padding=0))
        conv_layers.append(nn.BatchNorm2d(median_channels))
        conv_layers.append(nn.ReLu())
        if depth_wise :
            conv_layers.append(nn.Conv2d(in_channels=median_channels, out_channels=median_channels, kernel_size=3, stride=1, padding=1, groups=median_channels))
            conv_layers.append(nn.Conv2d(in_channels=median_channels, out_channels=median_channels, kernel_size=1, stride=1, padding=0))
        else :  
            conv_layers.append(in_channels=median_channels, out_channels=median_channels, kernel_size=3, stride=1, padding=1)
        conv_layers.append(nn.BatchNorm2d(median_channels))
        conv_layers.append(nn.ReLu())
        conv_layers.append(nn.Conv2d(in_channels=median_channels, out_channels=in_channels, kernel_size=1, stride=1, padding=0))
        conv_layers.append(nn.BatchNorm2d(in_channels))
        conv_layers.append(nn.ReLu())
        self.conv_blocks = nn.Sequential(*conv_layers)        
    def forward(self, x):
        
        output = self.conv_blocks(x)
        
        return output
    
class InceptionBlock(nn.Module):
    """
    This block takes an input with in_channels and applies 4 different
    convolutional layers to it. The output is the concatenation of the
    4 outputs.
    """

    def __init__(self,in_channels):
        super(InceptionBlock, self).__init__()
        
        self.conv1x1_1 = nn.Conv2d(in_channels=in_channels, out_channels=in_channels//2, kernel_size=1, stride=1, padding=0)

        out_1 = in_channels//4
        self.conv1x1_2 = nn.Conv2d(in_channels=in_channels, out_channels=out_1, kernel_size=1, stride=1, padding=0)
        self.conv3x3 = nn.Conv2d(in_channels=out_1, out_channels=3*out_1, kernel_size=3, stride=1, padding=1)
        
        self.conv1x1_3 = nn.Conv2d(in_channels=in_channels, out_channels=out_1, kernel_size=1, stride=1, padding=0)
        self.conv5x5 = nn.Conv2d(in_channels=out_1, out_channels=(3*out_1)//2, kernel_size=1, stride=1, padding=0)
        
        self.conv1x1_4 = nn.Conv2d(in_channels=in_channels, out_channels=out_1, kernel_size=1, stride=1, padding=0)
        
    def forward(self, x):
        
        branch_1 = F.relu(self.conv1x1_1(x))
        
        branch_2 = F.relu(self.conv3x3(F.relu(self.conv1x1_2(x))))
        
        branch_3 = F.relu(self.conv5x5(F.relu(self.conv1x1_3(x))))
        
        branch_4 = F.relu(self.conv1x1_4(F.max_pool2d(x, kernel_size=3, stride=1, padding=1)))
        
        output = torch.cat((branch_1, branch_2, branch_3, branch_4), 1)
        
        return output
    
class SqueezeAndExciteBlock(nn.Module):
    """
    This block takes an input with in_channels and applies a squeeze and excitation
    operation to it. It first applies a global average pooling to the input, then
    applies 2 fully connected layers with ReLU activations and finally applies a
    sigmoid activation to the output. It multiplies the input by the output.
    """
    
    def __init__(self,in_channels,downsample):
        super(SqueezeAndExciteBlock,self).__init__()
        median_channels = in_channels // downsample
        self.fully_connected_1 = nn.Linear(in_channels, median_channels)
        self.fully_connected_2 = nn.Linear(median_channels, in_channels)
        
    def forward(self, x):
        
        output = F.adaptive_avg_pool2d(x, (1,1))
        output = output.view(output.size(0), -1)
        output = F.relu(self.fully_connected_1(output))
        output = self.fully_connected_2(output)
        output = F.sigmoid(output)
        
        output = output.view(output.size(0), -1, 1, 1)
        output = x * output
        output = torch.cat((x, output), 1)
        return output