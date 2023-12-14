from functools import partial
import itertools
from tkinter.messagebox import NO

from torchnmf.nmf import NMF
from nimfa.methods.seeding import Nndsvd
from nimfa.methods.factorization import Nmf, Nsnmf

from _config import *
from _shared_imports import *
import scipy.io as spio
import torchvision
from sys import exit
from sklearn.utils.class_weight import compute_class_weight



def load_csv_data(path, labels_column=-1):
	"""
	Load a data file
	- path (str): path to csv_file
	- labels_column (int): indice of the column with labels
	"""
	Xy = pd.read_csv(path, index_col=0)
	X = Xy[Xy.columns[:labels_column]].to_numpy()
	y = Xy[Xy.columns[labels_column]].to_numpy()

	return X, y

def load_cohort(cohort_id, filter_genes, label_column_name='ClaudinSubtype'):
	"""
	Return the cohort `cohort_id`

	:param cohort_id (int): The id of the cohort (0, 1, 2, 3, 4)
	:param filter_genes (bool): If `True`, return the intersection with the genes from `imp_genes_list.csv`
	:param label_column_name (string): The name of the label column in the dataframes
	"""
	data = pd.read_csv(os.path.join(DATA_DIR, f'metabric_sample85_{cohort_id}.csv'), index_col=0)
	
	X = data.drop(columns=data.columns[:27])
	y = data[label_column_name]
	
	if filter_genes:
		genes_to_filter = pd.read_csv(os.path.join(DATA_DIR, f'imp_genes_list.csv'))

		X = X.drop(columns=list(set.difference(set(X.columns), set(genes_to_filter['gene']))))

	# Drop datapoints with ClaudinSubtype == 1
	if label_column_name == 'ClaudinSubtype':
		X = X[y != 1]
		y = y[y !=1 ]

	return X, y


def load_pam50_non3neg():
	"""
	Returns all patients that are not triple negatives
	"""
	data = pd.read_csv(f'/Users/andrei/Documents/GitHub/cancer-low-data/low_data_samples/PAM50/metabrick_non3neg_pam50.csv', index_col=0)
	data = data.dropna()
	X_mrna = data.drop(columns=data.columns[:26])

	"""
	The initial label are ['Pam50Subtype'] {'Normal':0, 'LumA':1, 'Her2':2, 'Basal':3, 'LumB': 4}
	Combine them into a new binary classification task: Basal (target 1) vs Non-basal (target 0)
	"""
	new_labels = {0:0, 1:0, 2:0, 3:1, 4:0}
	y = data['Pam50Subtype'].apply(lambda x: new_labels[x])

	# the genes are already filtered to the 4160 from partner
	print(f"loaded_pam50_non3neg dataset of size {X_mrna.shape}")

	return X_mrna, y


def load_pam50_3neg():
	"""
	Returns all patients that are not triple negatives
	"""
	data = pd.read_csv(f'/Users/andrei/Documents/GitHub/cancer-low-data/low_data_samples/PAM50/metabrick_3neg_pam50.csv', index_col=0)
	X_mrna = data.drop(columns=data.columns[:26])

	"""
	The initial label are ['Pam50Subtype'] {'Normal':0, 'LumA':1, 'Her2':2, 'Basal':3, 'LumB': 4}
	Combine them into a new binary classification task: Basal (target 1) vs Non-basal (target 0)
	"""
	new_labels = {0:0, 1:0, 2:0, 3:1, 4:0}
	y = data['Pam50Subtype'].apply(lambda x: new_labels[x])

	# the genes are already filtered to the 4160 from partner
	print(f"loaded_pam50_3neg dataset of size {X_mrna.shape}")

	return X_mrna, y


def load_pam50_cohort(cohort_id, filter_genes=True):
	"""
	Return the cohort `cohort_id`

	:param cohort_id (int): The id of the cohort (0, 1, 2, 3, 4)
	:param filter_genes (bool): If `True`, return the intersection with the genes from `imp_genes_list.csv`
	"""
	data = pd.read_csv(f'/Users/andrei/Documents/GitHub/cancer-low-data/low_data_samples/PAM50/metabric_sample85_PAM50_{cohort_id}.csv', index_col=0)
	X_mrna = data.drop(columns=data.columns[:27])
	X_cna = pd.read_csv(f'/Users/andrei/Documents/GitHub/cancer-low-data/low_data_samples/PAM50/metabric_sample85_PAM50_{cohort_id}_cna.csv', index_col=0)


	"""
	The initial label are ['Pam50Subtype'] {'Normal':0, 'LumA':1, 'Her2':2, 'Basal':3}
	Combine them into a new binary classification task: Basal (target 1) vs Non-basal (target 0)
	"""
	new_labels = {0:0, 1:0, 2:0, 3:1}
	y = data['Pam50Subtype'].apply(lambda x: new_labels[x])

	#### process mRNA data
	if filter_genes:
		genes_to_filter = pd.read_csv(os.path.join('/Users/andrei/Documents/GitHub/cancer-low-data/data', f'imp_genes_list.csv'))

		X_mrna = X_mrna.drop(columns=list(set.difference(set(X_mrna.columns), set(genes_to_filter['gene']))))
		X_cna = X_cna.drop(columns=list(set.difference(set(X_cna.columns), set(genes_to_filter['gene']))))

	return X_mrna, X_cna, y


def load_lung(drop_class_5=True):
	"""
	Labels in initial dataset:
	1    139
	2     17
	3     21
	4     20
	5      6

	We drop the class 5 because it has too little examples.
	"""
	data = spio.loadmat(f'{DATA_DIR}/lung.mat')
	X = pd.DataFrame(data['X'])
	Y = pd.Series(data['Y'][:, 0])

	if drop_class_5:
		# Examples of class 5 are deleted
		X = X.drop(index=[156, 157, 158, 159, 160, 161])
		Y = Y.drop([156, 157, 158, 159, 160, 161])

	new_labels = {1:0, 2:1, 3:2, 4:3, 5:4}
	Y = Y.apply(lambda x: new_labels[x])

	return X, Y

def load_prostate():
	""""
	Labels in initial dataset:
	1    50
	2    52
	"""
	data = spio.loadmat(f'{DATA_DIR}/Prostate_GE.mat')
	X = pd.DataFrame(data['X'])
	Y = pd.Series(data['Y'][:, 0])

	new_labels = {1:0, 2:1}
	Y = Y.apply(lambda x: new_labels[x])

	return X, Y

def load_toxicity():
	"""
	Labels in initial dataset:
	1    45
	2    45
	3    39
	4    42
	"""
	data = spio.loadmat(f'{DATA_DIR}/TOX_171.mat')
	X = pd.DataFrame(data['X'])
	Y = pd.Series(data['Y'][:, 0])

	new_labels = {1:0, 2:1, 3:2, 4:3}
	Y = Y.apply(lambda x: new_labels[x])

	return X, Y

def load_cll():
	"""
	Labels in initial dataset:
	1    11
	2    49
	3    51
	"""
	data = spio.loadmat(f'{DATA_DIR}/CLL_SUB_111.mat')
	X = pd.DataFrame(data['X'])
	Y = pd.Series(data['Y'][:, 0])

	new_labels = {1:0, 2:1, 3:2}
	Y = Y.apply(lambda x: new_labels[x])

	return X, Y

def load_smk():
	"""
	Labels in initial dataset:
	1    90
	2    97
	"""
	data = spio.loadmat(f'{DATA_DIR}/SMK_CAN_187.mat')
	X = pd.DataFrame(data['X'])
	Y = pd.Series(data['Y'][:, 0])

	new_labels = {1:0, 2:1}
	Y = Y.apply(lambda x: new_labels[x])

	return X, Y

def load_simple_synth():
    data = pd.read_csv(f'{DATA_DIR}/SyntheticData/simple_synthetic_dataset.csv', names=['x1','x2','x3','x4','x5','y'])
    X = data[['x1','x2','x3','x4','x5']]
    Y = data['y']
    return X, Y

def sample_dataset(args, dataset, label, train_size, valid_size, test_size):
	#### Set train/valid/test sizes
	# Create test set
	dataset_train_valid, dataset_test = train_test_split(dataset, test_size=test_size, 
			random_state=args.repeat_id, shuffle=True, stratify=dataset[label])
	# Create validation set
	dataset_train_large, dataset_valid = train_test_split(dataset_train_valid, test_size=valid_size,
			random_state=args.repeat_id, shuffle=True, stratify=dataset_train_valid[label])
	
	# Create train set (dataset_train contains too many entries. We select only a subset of it)
	dataset_train, _ = train_test_split(dataset_train_large, train_size=train_size,
			random_state=args.repeat_id, shuffle=True, stratify=dataset_train_large[label])

	return dataset_train[dataset_train.columns[:-1]].to_numpy(), dataset_train[dataset_train.columns[-1]].to_numpy(), \
		   dataset_valid[dataset_valid.columns[:-1]].to_numpy(), dataset_valid[dataset_valid.columns[-1]].to_numpy(), \
		   dataset_test[dataset_test.columns[:-1]].to_numpy(), dataset_test[dataset_test.columns[-1]].to_numpy() 


def sample_metabric_dataset(args, train_size, valid_size, test_size):
	"""
	Sample Metabric dataset on the fly, with custom train/valid/test sizes.
	"""
	#### Load expression data
	expressionsMB = pd.read_csv(f'{DATA_DIR}/Metabric_full/MOLECULARDATA/CURTIS_data_Expression.txt', delimiter='\t').T

	# set columns
	expressionsMB.columns = expressionsMB.iloc[0]
	# drop two rows that contain column names
	expressionsMB.drop(expressionsMB.index[[0,1]], inplace=True)
	expressionsMB_genes = expressionsMB.T.copy()

	# load Hallmark gene set
	genes_to_filter = pd.read_csv(f'{DATA_DIR}/imp_genes_list.csv',index_col=0)
	genes_to_filter_unduplicated = genes_to_filter.loc[~genes_to_filter.index.duplicated(keep='first')]

	# keep only the genes from Hallmark
	expressionsMB_filtered = pd.concat([genes_to_filter_unduplicated, expressionsMB_genes],axis=1, join="inner").copy()
	expressionsMB_filtered = expressionsMB_filtered.T.copy().dropna()
	

	#### Load clinical data
	clinMB = pd.read_csv(f'{DATA_DIR}/Metabric_full/MOLECULARDATA/TableS6.txt', delimiter='\t')
	clinMB.set_index('METABRIC.ID',inplace=True)


	#### Set task
	if args.dataset == 'metabric-dr':
		DR = clinMB['DR'].copy().dropna()
		dataset = expressionsMB_filtered.merge(DR, left_index=True, right_index=True, validate='one_to_one')
		label = 'DR'
	elif args.dataset == 'metabric-pam50':
		pam50 = clinMB['Pam50Subtype'].copy().dropna()
		pam50_binary = pam50.map({
			'Basal': int(1), 
			'LumA': int(0),
			'LumB': int(0),
			'Her2': int(0),
			'Normal': int(0)
		}).astype(int)

		dataset = expressionsMB_filtered.merge(pam50_binary, left_index=True, right_index=True, validate='one_to_one')
		label = 'Pam50Subtype'
	else:
		raise ValueError(f'Unknown dataset {args.dataset}')

	return sample_dataset(args, dataset, label, train_size, valid_size, test_size)


def sample_tcga_dataset(args, train_size, valid_size, test_size):
	tcga_full = pd.read_csv(f'{DATA_DIR}/TCGA_full/tcga_hncs.csv', index_col=0)
	tcga_full = tcga_full.dropna()

	# filter genes
	partner_genes_to_filter = pd.read_csv(f'{DATA_DIR}/imp_genes_list.csv',index_col=0)
	set_partner_genes_to_filter = set(partner_genes_to_filter.index)

	# Clean the set of columns to match the Partner Naming
	column_names_clean = []
	for column_with_number in tcga_full.columns:
		column_name = column_with_number.split('|')[0]
		column_names_clean.append(column_name)
	
	genes_intersection = list(set(column_names_clean).intersection(set_partner_genes_to_filter))
	genes_intersection = sorted(genes_intersection)

	# keep only the Partner set of genes
	tcga_full_columns_changed = tcga_full.copy()
	tcga_full_columns_changed.columns = column_names_clean
	tcga_only_intersection_genes = tcga_full_columns_changed[genes_intersection]

	if args.dataset == 'tcga-tumor-grade':
		tcga_genes_and_tumor_grade = tcga_only_intersection_genes.copy()
		tcga_genes_and_tumor_grade = tcga_genes_and_tumor_grade.merge(tcga_full['tumor_grade'], left_index=True, right_index=True, validate='one_to_one')
		
		# Keep only G1, G2, G3 classes
		tcga_genes_and_tumor_grade = tcga_genes_and_tumor_grade.loc[tcga_genes_and_tumor_grade['tumor_grade'].isin(['G1', 'G2', 'G3'])]
		tcga_genes_and_tumor_grade['tumor_grade'] = tcga_genes_and_tumor_grade['tumor_grade'].map({'G1': int(0), 'G2': int(1), 'G3': int(2)})
		dataset = tcga_genes_and_tumor_grade
		
		label = 'tumor_grade'
	elif args.dataset == 'tcga-2ysurvival':
		tcga_genes_and_2ysurvival = tcga_only_intersection_genes.copy()
		dataset = tcga_genes_and_2ysurvival.merge(tcga_full['X2yr.RF.Surv.'], left_index=True, right_index=True, validate='one_to_one')

		label = 'X2yr.RF.Surv.'
	else:
		raise ValueError(f'Unknown dataset {args.dataset}')

	return sample_dataset(args, dataset, label, train_size, valid_size, test_size)


class CustomPytorchDataset(Dataset):
	def __init__(self, X, y, transform=None) -> None:
		# X, y are numpy
		super().__init__()

		self.X = torch.tensor(X, requires_grad=False)
		self.y = torch.tensor(y, requires_grad=False)
		self.transform = transform

	def __getitem__(self, index):
		x = self.X[index]
		y = self.y[index]
		if self.transform:
			x = self.transform(x)
			y = y.repeat(x.shape[0]) # replicate y to match the size of x

		return x, y

	def __len__(self):
		return len(self.X)


def standardize_data(X_train, X_valid, X_test, preprocessing_type):
	if preprocessing_type == 'standard':
		scaler = StandardScaler()
	elif preprocessing_type == 'minmax':
		scaler = MinMaxScaler()
	elif preprocessing_type == 'raw':
		scaler = None
	else:
		raise Exception("preprocessing_type not supported")

	if scaler:
		X_train = scaler.fit_transform(X_train).astype(np.float32)
		X_valid = scaler.transform(X_valid).astype(np.float32)
		X_test = scaler.transform(X_test).astype(np.float32)

	return X_train, X_valid, X_test


def compute_stratified_splits(X, y, cv_folds, seed_kfold, split_id):
	skf = StratifiedKFold(n_splits=cv_folds, shuffle=True, random_state=seed_kfold)
	
	for i, (train_ids, test_ids) in enumerate(skf.split(X, y)):
		if i == split_id:
			return X[train_ids], X[test_ids], y[train_ids], y[test_ids]


###############    EMBEDDINGS     ###############

def compute_histogram_embedding(args, X, embedding_size):
	"""
	Compute embedding_matrix (D x M) based on the histograms. The function implements two methods:

	DietNetwork
	- Normalized bincounts for each SNP

	FsNet
	0. Input matrix NxD
	1. Z-score standardize each column (mean 0, std 1)
	2. Compute the histogram for every feature (with density = False)
	3. Multiply the histogram values with the bin mean

	:param (N x D) X: dataset, each row representing one sample
	:return np.ndarray (D x M) embedding_matrix: matrix where each row represents the embedding of one feature
	"""
	X = np.rot90(X)
	
	number_features = X.shape[0]
	embedding_matrix = np.zeros(shape=(number_features, embedding_size))

	for feature_id in range(number_features):
		feature = X[feature_id]

		hist_values, bin_edges = np.histogram(feature, bins=embedding_size) # like in FsNet
		bin_centers = (bin_edges[1:] + bin_edges[:-1])/2
		embedding_matrix[feature_id] = np.multiply(hist_values, bin_centers)

	return embedding_matrix


def compute_nmf_embeddings(Xt, rank):
	"""
	Note: torchnmf computes V = H W^T instead of the standard formula V = W H

	Input
	- V (D x N)
	- rank of NMF

	Returns
	- H (D x r) (torch.Parameter with requires_grad=True), where each row represents one gene embedding 
	"""
	print("Approximating V = H W.T")
	print(f"Input V has shape {Xt.shape}")
	assert type(Xt)==torch.Tensor
	assert Xt.shape[0] > Xt.shape[1]

	nmf = NMF(Xt.shape, rank=rank).cuda()
	nmf.fit(Xt.cuda(), beta=2, max_iter=1000, verbose=True) # beta=2 coresponds to the Frobenius norm, which is equivalent to an additive Gaussian noise model

	print(f"H has shape {nmf.H.shape}")
	print(f"W.T has shape {nmf.W.T.shape}")

	return nmf.H, nmf.W


def compute_nmf_nimfa_embeddings(X, rank):
	"""
	Note: torchnmf computes V = H W^T instead of the standard formula V = W H

	Input
	- V (N x D)
	- rank of NMF

	Returns
	- H (D x r) (torch.Parameter with requires_grad=True), where each row represents one gene embedding 
	"""
	print("Approximating V = H W")
	if type(X)==torch.Tensor:
		if X.device == torch.device('cpu'):
			X = X.detach().numpy()
		else:
			X = X.detach().cpu().numpy()

	nmf = Nmf(X, rank=rank, max_iter=100)
	nmf_fit = nmf()
	W = nmf_fit.basis() # N x r
	H = nmf_fit.coef()	# r x D

	print(f"W has shape {W.shape}")
	print(f"H.T has shape {H.shape}")

	return torch.tensor(H.T, dtype=torch.float32, device=torch.device('cuda')), \
		   torch.tensor(W, dtype=torch.float32, device=torch.device('cuda'))


def compute_svd_embeddings(X, rank=None):
	"""
	- X (N x D)
	- rank (int): rank of the approximation (i.e., size of the embedding)
	"""
	assert type(X)==torch.Tensor
	assert X.shape[0] < X.shape[1]

	U, S, Vh = torch.linalg.svd(X, full_matrices=False)

	V = Vh.T

	if rank:
		S = S[:rank]
		V = V[:rank]

	return V, S


###############    DATASETS     ###############

class DatasetModule(pl.LightningDataModule):
	def __init__(self, args, X_train, y_train, X_valid, y_valid, X_test, y_test):
		super().__init__()
		self.args = args

		args.num_features = X_train.shape[1]
		args.num_classes = len(set(y_train).union(set(y_valid)).union(set(y_test)))

		# Standardize data
		self.X_train_raw = X_train
		self.X_valid_raw = X_valid
		self.X_test_raw = X_test

		X_train, X_valid, X_test = standardize_data(X_train, X_valid, X_test, args.patient_preprocessing)
		
		self.X_train = X_train
		self.y_train = y_train
		self.X_valid = X_valid
		self.y_valid = y_valid
		self.X_test = X_test
		self.y_test = y_test

		self.train_dataset = CustomPytorchDataset(X_train, y_train)
		self.valid_dataset = CustomPytorchDataset(X_valid, y_valid)
		self.test_dataset = CustomPytorchDataset(X_test, y_test)

		self.args.train_size = X_train.shape[0]
		self.args.valid_size = X_valid.shape[0]
		self.args.test_size = X_test.shape[0]

		# store the names of the validation dataloaders. They are appended to validation metrics
		self.val_dataloaders_name = [""] # the valid dataloader with the original data has no special name

	def train_dataloader(self):
		return DataLoader(self.train_dataset, batch_size=self.args.batch_size, shuffle=True, drop_last=True,
							num_workers=self.args.num_workers, pin_memory=self.args.pin_memory)

	def val_dataloader(self):
		# dataloader with original samples
		dataloaders = [DataLoader(self.valid_dataset, batch_size=128, num_workers=self.args.num_workers, pin_memory=self.args.pin_memory)]

		# dataloaders for each validation augmentation type
		if self.args.valid_aug_dropout_p:
			if self.args.valid_aug_times==None:
				raise Exception("You must supply a list of --valid_aug_times.")

			# define some transformations
			def dropout_transform(x, p):
				"""
				- x (tensor): one datapoint
				- p (float): probability of droppint out features
				"""
				return F.dropout(x, p, training=True)

			def multiplicity_transform(x, no_times, transform):
				"""
				Args:
				- no_times (int): number of times to apply the transformation `transform`
				- transform (function): the tranformation function to be applied `no_times` times
				
				Return
				- stacked 2D tensor with the original samples and its augmented versions
				"""
				samples = [transform(x) for _ in range(no_times)]
				samples.append(x)

				return torch.stack(samples)

			for dropout_p, aug_times in itertools.product(self.args.valid_aug_dropout_p, self.args.valid_aug_times):
				partial_dropout_transform = partial(dropout_transform, p=dropout_p)
				print(f"Create validation dataset with dropout_p={dropout_p} and aug_times={aug_times}")
				partial_multiplicity_transform = partial(multiplicity_transform, no_times=aug_times, transform=partial_dropout_transform)
				
				valid_dataset_augmented = CustomPytorchDataset(self.X_valid, self.y_valid, transform=torchvision.transforms.Compose([
					torchvision.transforms.Lambda(partial_multiplicity_transform)
				]))

				dataloaders.append(DataLoader(valid_dataset_augmented, batch_size=self.args.batch_size, num_workers=self.args.num_workers, pin_memory=self.args.pin_memory))
				self.val_dataloaders_name.append(f'dropout_p_{dropout_p}__aug_times_{aug_times}')
		
		print(f"Created {len(dataloaders)} validation dataloaders.")
		self.args.val_dataloaders_name = self.val_dataloaders_name # save the name to args, to be able to access them in the model (and use for logging)
		return dataloaders


	def test_dataloader(self):
		return DataLoader(self.test_dataset, batch_size=128, num_workers=self.args.num_workers, pin_memory=self.args.pin_memory)

	def get_embedding_matrix(self, embedding_type, embedding_size):
		"""
		Return matrix D x M

		Use a the shared hyper-parameter self.args.embedding_preprocessing.
		"""
		if embedding_type == None:
			return None
		else:
			if embedding_size == None:
				raise Exception()

		# Preprocess the data for the embeddings
		if self.args.embedding_preprocessing == 'raw':
			X_for_embeddings = self.X_train_raw
		elif self.args.embedding_preprocessing == 'standard':
			X_for_embeddings = StandardScaler().fit_transform(self.X_train_raw)
		elif self.args.embedding_preprocessing == 'minmax':
			X_for_embeddings = MinMaxScaler().fit_transform(self.X_train_raw)
		else:
			raise Exception("embedding_preprocessing not supported")

		if embedding_type == 'histogram':
			"""
			Embedding similar to FsNet
			"""
			embedding_matrix = compute_histogram_embedding(self.args, X_for_embeddings, embedding_size)
			return torch.tensor(embedding_matrix.copy(), dtype=torch.float32, requires_grad=False)
		elif embedding_type=='all_patients':
			"""
			A gene's embedding are its patients gene expressions.
			"""
			embedding_matrix = np.rot90(X_for_embeddings)[:, :embedding_size]
			return torch.tensor(embedding_matrix.copy(), dtype=torch.float32, requires_grad=False)
		elif embedding_type=='svd':
			# Vh.T (4160 x rank) contains the gene embeddings on each row
			U, S, Vh = torch.linalg.svd(torch.tensor(X_for_embeddings, dtype=torch.float32), full_matrices=False) 
			
			Vh.T.requires_grad = False
			return Vh.T[:, :embedding_size].type(torch.float32)
		elif embedding_type=='nmf':
			H, _ = compute_nmf_embeddings(torch.tensor(X_for_embeddings).T, rank=embedding_size)
			H_data = H.data
			H_data.requires_grad = False
			return H_data.type(torch.float32)
		else:
			raise Exception("Invalid embedding type")


def create_data_module(args):
	if "__" in args.dataset:	# used when instantiang the model from wandb artifacts
		dataset, dataset_size = args.dataset.split("__")
	else:
		dataset, dataset_size = args.dataset, args.dataset_size

	if args.evaluate_with_sampled_datasets:
		if dataset in ['metabric-pam50', 'metabric-dr']:
			X_train, y_train, X_valid, y_valid, X_test, y_test = sample_metabric_dataset(
				args, args.custom_train_size, args.custom_valid_size, args.custom_test_size)
		elif dataset in ['tcga-2ysurvival', 'tcga-tumor-grade']:
			X_train, y_train, X_valid, y_valid, X_test, y_test = sample_tcga_dataset(
				args, args.custom_train_size, args.custom_valid_size, args.custom_test_size)
		else:
			raise Exception("Dataset not supported")

		data_module = DatasetModule(args, X_train, y_train, X_valid, y_valid, X_test, y_test)
	else:
		if dataset in ['metabric-pam50', 'metabric-dr', 'tcga-2ysurvival', 'tcga-tumor-grade']:
			# compute paths
			if dataset=='metabric-pam50':
				if args.dataset_feature_set=='hallmark':
					args.train_path=f'{DATA_DIR}/Metabric_samples/metabric_pam50_train_{dataset_size}.csv'
					args.test_path=f'{DATA_DIR}/Metabric_samples/metabric_pam50_test_100.csv'
				else:
					args.train_path=f'{DATA_DIR}/Metabric_samples/metabric_pam50_all_genes_train_{dataset_size}.csv'
			elif dataset=='metabric-dr':
				if args.dataset_feature_set=='hallmark':
					args.train_path=f'{DATA_DIR}/Metabric_samples/metabric_DR_train_{dataset_size}.csv'
					args.test_path=f'{DATA_DIR}/Metabric_samples/metabric_DR_test_100.csv'
				else:
					args.train_path=f'{DATA_DIR}/Metabric_samples/metabric_DR_all_genes_train_{dataset_size}.csv'
			elif dataset=='tcga-2ysurvival':
				args.train_path=f'{DATA_DIR}/TCGA_samples/tcga_2ysurvival_train_{dataset_size}.csv'
				args.test_path=f'{DATA_DIR}/TCGA_samples/tcga_2ysurvival_test_100.csv'
			elif dataset=='tcga-tumor-grade':
				args.train_path=f'{DATA_DIR}/TCGA_samples/tcga_tumor_grade_train_{dataset_size}.csv'
				args.test_path=f'{DATA_DIR}/TCGA_samples/tcga_tumor_grade_test_100.csv'

			if args.testing_type=='fixed':
				data_module = create_datamodule_with_fixed_test(args, args.train_path, args.test_path)
			elif args.testing_type=='cross-validation':
				X, y = load_csv_data(args.train_path)
				data_module = create_datamodule_with_cross_validation(args, X, y)
		elif dataset in ['lung', 'toxicity', 'prostate', 'cll', 'smk', 'simple_synth']:
			if dataset=='lung':
				X, y = load_lung()
			elif dataset=='toxicity':
				X, y = load_toxicity()
			elif dataset=='prostate':
				X, y = load_prostate()
			elif dataset=='cll':
				X, y = load_cll()
			elif dataset=='smk':
				X, y = load_smk()
			elif dataset=='simple_synth':
				X, y = load_simple_synth()
			data_module = create_datamodule_with_cross_validation(args, X, y)

	#### Compute classification loss weights
	if args.class_weight=='balanced':
		args.class_weights = compute_class_weight(class_weight='balanced', classes=np.unique(data_module.y_train), y=data_module.y_train)
	elif args.class_weight=='standard':
		args.class_weights = compute_class_weight(class_weight=None, classes=np.unique(data_module.y_train), y=data_module.y_train)
	args.class_weights = args.class_weights.astype(np.float32)
	print(f"Weights for the classification loss: {args.class_weights}")

	return data_module


def create_datamodule_with_cross_validation(args, X, y):
	"""
	Split X, y to be suitable for nested cross-validation.
	It uses args.valid_split and args.test_split to create 
		the train, valid and test stratified datasets.
	"""
	if type(X)==pd.DataFrame:
		X = X.to_numpy()
	if type(y)==pd.Series:
		y = y.to_numpy()
	
	if args.dataset_feature_set=='8000':
		X = X[:, :8000]
	elif args.dataset_feature_set=='16000':
		X = X[:, :16000]

	assert type(X)==np.ndarray
	assert type(y)==np.ndarray

	X_train_and_valid, X_test, y_train_and_valid, y_test = compute_stratified_splits(
		X, y, cv_folds=args.cv_folds, seed_kfold=args.seed_kfold, split_id=args.test_split)

	# Split validation set
	X_train, X_valid, y_train, y_valid = train_test_split(
		X_train_and_valid, y_train_and_valid,
		test_size = args.valid_percentage,
		random_state = args.seed_validation,
		stratify = y_train_and_valid
	)
	
	print(f"Train size: {X_train.shape[0]}\n")
	print(f"Valid size: {X_valid.shape[0]}\n")
	print(f"Test size: {X_test.shape[0]}\n")

	assert X_train.shape[0] + X_valid.shape[0] + X_test.shape[0] == X.shape[0]
	assert set(y_train).union(set(y_valid)).union(set(y_test)) == set(y)

	if args.train_on_full_data:
		# Train on the entire training set (train + validation)
		# Validation and test sets are the same
		return DatasetModule(args, X_train_and_valid, y_train_and_valid, X_test, y_test, X_test, y_test)
	else:
		return DatasetModule(args, X_train, y_train, X_valid, y_valid, X_test, y_test)
	

def create_datamodule_with_fixed_test(args, train_path, test_path):
	"""
	Data module suitable when all the splits are pre-made and ready to load from their path.    
	By **convention**, the label is on the last column.
	"""
	assert args.valid_split < args.cv_folds
	assert test_path!=None

	# Load data. By convention the last column is the target
	X_test, y_test = load_csv_data(test_path, labels_column=-1)
	X_train_and_valid, y_train_and_valid = load_csv_data(train_path, labels_column=-1)
	
	# Make CV splits
	X_train, X_valid, y_train, y_valid = compute_stratified_splits(
		args, X_train_and_valid, y_train_and_valid, split_id=args.valid_split)

	assert X_train.shape[0] + X_valid.shape[0] == X_train_and_valid.shape[0]
	assert set(y_train).union(set(y_valid)) == set(y_train_and_valid) 

	return DatasetModule(args, X_train, y_train, X_valid, y_valid, X_test, y_test)