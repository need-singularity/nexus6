"""Dataset loading utilities."""

from torch.utils.data import DataLoader

DATASETS = {
    'mnist': dict(
        dim=784,
        norm=(0.1307, 0.3081),
        cls_names=[str(i) for i in range(10)],
    ),
    'fashion': dict(
        dim=784,
        norm=(0.2860, 0.3530),
        cls_names=['Tshirt', 'Trouser', 'Pullvr', 'Dress', 'Coat',
                   'Sandal', 'Shirt', 'Sneakr', 'Bag', 'Boot'],
    ),
    'cifar': dict(
        dim=3072,
        norm=((0.5, 0.5, 0.5), (0.5, 0.5, 0.5)),
        cls_names=['plane', 'auto', 'bird', 'cat', 'deer',
                   'dog', 'frog', 'horse', 'ship', 'truck'],
    ),
}


def load_data(name, batch_size=256, data_dir='/tmp/data'):
    """Load a dataset.

    Args:
        name: One of 'mnist', 'fashion', 'cifar'
        batch_size: Training batch size
        data_dir: Path to store downloaded data

    Returns:
        Tuple of (input_dim, train_loader, test_loader, class_names)
    """
    from torchvision import datasets, transforms

    cfg = DATASETS[name]
    n = cfg['norm']
    mean, std = (n[0], n[1]) if isinstance(n[0], tuple) else ((n[0],), (n[1],))

    t = transforms.Compose([
        transforms.ToTensor(),
        transforms.Normalize(mean, std),
    ])

    DS = {
        'mnist': datasets.MNIST,
        'fashion': datasets.FashionMNIST,
        'cifar': datasets.CIFAR10,
    }[name]

    train_ds = DS(data_dir, train=True, download=True, transform=t)
    test_ds = DS(data_dir, train=False, download=True, transform=t)

    train_loader = DataLoader(train_ds, batch_size=batch_size, shuffle=True)
    test_loader = DataLoader(test_ds, batch_size=512, shuffle=False)

    return cfg['dim'], train_loader, test_loader, cfg['cls_names']
