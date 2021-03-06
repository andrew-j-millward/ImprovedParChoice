import torch, argparse, os
import time
from data import load_dataset
from models import StyleTransformer, Discriminator
from train import train, auto_eval, test_eval


class Config():
    data_path = './data/trump_elon/'
    log_dir = 'runs/exp'
    save_path = './save'
    pretrained_embed_path = './embedding/'
    device = torch.device('cuda' if True and torch.cuda.is_available() else 'cpu')
    discriminator_method = 'Multi' # 'Multi' or 'Cond'
    load_pretrained_embed = False
    min_freq = 3
    max_length = 64
    embed_size = 256
    d_model = 256
    h = 4
    num_styles = 2
    num_classes = num_styles + 1 if discriminator_method == 'Multi' else 2
    num_layers = 4
    batch_size = 32
    lr_F = 0.0001
    lr_D = 0.0001
    L2 = 0
    iter_D = 10
    iter_F = 5
    F_pretrain_iter = 500
    log_steps = 5
    eval_steps = 25
    learned_pos_embed = True
    dropout = 0
    drop_rate_config = [(1, 0)]
    temperature_config = [(1, 0)]

    slf_factor = 0.25
    cyc_factor = 0.5
    adv_factor = 1

    inp_shuffle_len = 0
    inp_unk_drop_fac = 0
    inp_rand_drop_fac = 0
    inp_drop_prob = 0

    run_eval = False
    use_ref = False

def inference(config, fpath, dpath, src_train, src_dev, src_test, tgt_train, tgt_dev, tgt_test, verbose=True):
    if config.data_path == './':
        train_iters, dev_iters, test_iters, vocab = load_dataset(config, train_pos=src_train, train_neg=tgt_train, 
                                                                dev_pos=src_dev, dev_neg=tgt_dev,
                                                                test_pos=src_test, test_neg=tgt_test)
    else:
        train_iters, dev_iters, test_iters, vocab = load_dataset(config)    

    if verbose:
        print('Vocab size:', len(vocab))
    model_F = StyleTransformer(config, vocab).to(config.device)
    model_D = Discriminator(config, vocab).to(config.device)

    if verbose:
        print(config.discriminator_method)
    
    if fpath:
        model_F = StyleTransformer(config, vocab).to(config.device)
        model_F.load_state_dict(torch.load(fpath))
        model_F.eval()
    else:
        raise ValueError("Missing path to model_F")
    if dpath:
        model_D = StyleTransformer(config, vocab).to(config.device)
        model_D.load_state_dict(torch.load(dpath))
        model_D.eval()

    config.save_folder = config.save_path + '/' + str(time.strftime('%b%d%H%M%S', time.localtime()))
    os.makedirs(config.save_folder)
    os.makedirs(config.save_folder + '/inference')

    if verbose:
        print('Save Path:', config.save_folder)
    
    pos_iter = test_iters.pos_iter
    neg_iter = test_iters.neg_iter
    gold_text_neg, raw_output_neg, rev_output_neg = test_eval(vocab, model_F, neg_iter, 0)
    gold_text_pos, raw_output_pos, rev_output_pos = test_eval(vocab, model_F, pos_iter, 1)

    return rev_output_neg, rev_output_pos

def main():
    parser = argparse.ArgumentParser(description='Perform inference on saved model.')
    parser.add_argument('-f', '--fpath', metavar='', help='Path to saved model_F')
    parser.add_argument('-d', '--dpath', metavar='', help='Path to saved model_D')
    args = parser.parse_args()

    config = Config()
    if config.data_path == './data/trump_elon/':
        train_iters, dev_iters, test_iters, vocab = load_dataset(config, train_pos='trump_train.txt', train_neg='elon_train.txt', 
                                                                dev_pos='trump_dev.txt', dev_neg='elon_dev.txt',
                                                                test_pos='trump_test.txt', test_neg='elon_test.txt')
    else:
        train_iters, dev_iters, test_iters, vocab = load_dataset(config)    
    print('Vocab size:', len(vocab))
    model_F = StyleTransformer(config, vocab).to(config.device)
    model_D = Discriminator(config, vocab).to(config.device)
    print(config.discriminator_method)
    
    if args.fpath:
        model_F = StyleTransformer(config, vocab).to(config.device)
        model_F.load_state_dict(torch.load(args.fpath))
        model_F.eval()
    else:
        raise ValueError("Missing path to model_F")
    if args.dpath:
        model_D = StyleTransformer(config, vocab).to(config.device)
        model_D.load_state_dict(torch.load(args.dpath))
        model_D.eval()

    config.save_folder = config.save_path + '/' + str(time.strftime('%b%d%H%M%S', time.localtime()))
    os.makedirs(config.save_folder)
    os.makedirs(config.save_folder + '/inference')
    print('Save Path:', config.save_folder)
    
    pos_iter = test_iters.pos_iter
    neg_iter = test_iters.neg_iter
    gold_text_neg, raw_output_neg, rev_output_neg = test_eval(vocab, model_F, neg_iter, 0)
    gold_text_pos, raw_output_pos, rev_output_pos = test_eval(vocab, model_F, pos_iter, 1)
    with open(config.save_folder + '/inference/' + '/gold_elon_to_trump.txt', 'w') as f:
        for text in gold_text_neg:
            f.write(text + "\n")
    with open(config.save_folder + '/inference/' + '/raw_elon_to_trump.txt', 'w') as f:
        for text in raw_output_neg:
            f.write(text + "\n")
    with open(config.save_folder + '/inference/' + '/rev_elon_to_trump.txt', 'w') as f:
        for text in rev_output_neg:
            f.write(text + "\n")
    with open(config.save_folder + '/inference/' + '/gold_trump_to_elon.txt', 'w') as f:
        for text in gold_text_pos:
            f.write(text + "\n")
    with open(config.save_folder + '/inference/' + '/raw_trump_to_elon.txt', 'w') as f:
        for text in raw_output_pos:
            f.write(text + "\n")
    with open(config.save_folder + '/inference/' + '/rev_trump_to_elon.txt', 'w') as f:
        for text in rev_output_pos:
            f.write(text + "\n")
    

if __name__ == '__main__':
    main()
