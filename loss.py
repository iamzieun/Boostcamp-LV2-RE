import torch
import torch.nn as nn
import torch.nn.functional as F

class FocalLoss(nn.Module):
    def __init__(self, alpha=1, gamma=2, reduction='mean'):
        super(FocalLoss, self).__init__()
        self.alpha = alpha
        self.gamma = gamma
        self.reduction = reduction

    def forward(self, inputs, targets):
        ce_loss = nn.CrossEntropyLoss(reduction='none')(inputs, targets)
        pt = torch.exp(-ce_loss)
        focal_loss = self.alpha * (1 - pt)**self.gamma * ce_loss

        if self.reduction == 'mean':
            return torch.mean(focal_loss)
        elif self.reduction == 'sum':
            return torch.sum(focal_loss)
        else:
            return focal_loss
        

class LovaszSoftmaxLoss(nn.Module):
    def __init__(self, reduction='mean'):
        super(LovaszSoftmaxLoss, self).__init__()
        self.reduction = reduction

    def lovasz_grad(self, true_sorted):
        p = len(true_sorted)
        gts = true_sorted.sum()
        intersection = gts - true_sorted.cumsum(0)
        union = gts + (1 - true_sorted).cumsum(0)
        jaccard = 1 - intersection / union
        if p > 1:  # cover 1-pixel case
            jaccard[1:p] = jaccard[1:p] - jaccard[0:-1]
        return jaccard

    def lovasz_softmax(self, probas, labels):
        C = probas.shape[1]
        losses = []
        for c in range(C):
            fg = (labels == c).float()  # foreground for class c
            if fg.sum() == 0:
                continue
            errors = (fg - probas[:, c]).abs()
            errors_sorted, perm = torch.sort(errors, 0, descending=True)
            fg_sorted = fg[perm]
            losses.append(torch.dot(errors_sorted, self.lovasz_grad(fg_sorted)))
        return torch.stack(losses)

    def forward(self, inputs, targets):
        probas = F.softmax(inputs, dim=1)
        lovasz_loss = self.lovasz_softmax(probas, targets)

        if self.reduction == 'mean':
            return torch.mean(lovasz_loss)
        elif self.reduction == 'sum':
            return torch.sum(lovasz_loss)
        else:
            return lovasz_loss


