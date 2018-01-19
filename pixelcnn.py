import torch.nn as nn
import torch
import numpy as np
import pdb


class MaskedConv2d(nn.Conv2d):
    def __init__(self, mask_type, *args, **kwargs):
        super(MaskedConv2d, self).__init__(*args, **kwargs)
        n_out, n_in, h, w = self.weight.size()
        mask = torch.ones(n_out, n_in, h, w)
        ch = h // 2
        cw = w // 2
        if mask_type=='A':  # center=0
            mask[:, :, ch+1:, :] = 0
            mask[:, :, ch, cw:] = 0
        elif mask_type=='B':  # center=1
            mask[:, :, ch+1:, :] = 0
            mask[:, :, ch, cw+1:] = 0
        self.register_buffer('mask', mask)

    def forward(self, x):
        self.weight.data *= self.mask
        return super(MaskedConv2d, self).forward(x)

# def causal_mask(width, height, starting_point):
#     row_grid, col_grid = np.meshgrid(np.arange(width), np.arange(height), indexing='ij')
#     mask = np.logical_or(
#         row_grid < starting_point[0],
#         np.logical_and(row_grid == starting_point[0], col_grid <= starting_point[1]))
#     return mask
#
# def conv_mask(width, height, include_center=False):
#     return 1.0 * causal_mask(width, height, starting_point=(width//2, height//2 + include_center - 1))
#
# class MaskedConv2d(nn.Conv2d):
#     def __init__(self, mask_type, *args, **kwargs):
#         super(MaskedConv2d, self).__init__(*args, **kwargs)
#         _, n_channels, width, height = self.weight.size()
#
#         mask = conv_mask(width, height, include_center=mask_type=='B')
#         self.register_buffer('mask', torch.from_numpy(mask).float())
#
#     def forward(self, x):
#         self.weight.data *= self.mask
#         return super(MaskedConv2d, self).forward(x)

n_hidden = 2
d_hidden = 2
ksize = 3
class ResBlock(nn.Module):
    def __init__(self):
        super(ResBlock, self).__init__()
        self.main = nn.Sequential(
            nn.ReLU(),
            nn.Conv2d(2*n_hidden, n_hidden, kernel_size=1),
            nn.ReLU(),
            MaskedConv2d('B', n_hidden, n_hidden, kernel_size=ksize, stride=1, padding=ksize//2),
            nn.ReLU(),
            nn.Conv2d(n_hidden, 2*n_hidden, kernel_size=1),
        )

    def forward(self, x):
        return x+self.main(x)


class PixelCNN(nn.Module):
    def __init__(self):
        super(PixelCNN, self).__init__()
        self.main = nn.Sequential(
            MaskedConv2d('A', 1, 2*n_hidden, kernel_size=ksize, stride=1, padding=ksize//2),
            nn.ReLU(),
            ResBlock(),
            ResBlock(),
            ResBlock(),
            ResBlock(),
            ResBlock(),
            nn.ReLU(),
            nn.Conv2d(2*n_hidden, d_hidden, kernel_size=1),
            nn.ReLU(),
            nn.Conv2d(d_hidden, 1, kernel_size=1)
            # ResBlock(),
            # nn.ReLU(),
            # nn.Conv2d(2*n_hidden, d_hidden, kernel_size=1),
            # nn.ReLU(),
            # nn.Conv2d(d_hidden, 1, kernel_size=1)
        )

    def forward(self, x):
        return self.main(x)