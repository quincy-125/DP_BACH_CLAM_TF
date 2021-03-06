import os
import random
import shutil

import numpy as np
import tensorflow as tf
import tensorflow_addons as tfa


def get_data_from_tf(tf_path, imf_norm_op):
    feature = {'height': tf.io.FixedLenFeature([], tf.int64),
               'width': tf.io.FixedLenFeature([], tf.int64),
               'depth': tf.io.FixedLenFeature([], tf.int64),
               'label': tf.io.FixedLenFeature([], tf.int64),
               'image/format': tf.io.FixedLenFeature([], tf.string),
               'image_name': tf.io.FixedLenFeature([], tf.string),
               'image/encoded': tf.io.FixedLenFeature([], tf.string),
               'image_feature': tf.io.FixedLenFeature([], tf.string)}

    tfrecord_dataset = tf.data.TFRecordDataset(tf_path)

    def _parse_image_function(key):
        return tf.io.parse_single_example(key, feature)

    CLAM_dataset = tfrecord_dataset.map(_parse_image_function)

    image_features = list()

    for tfrecord_value in CLAM_dataset:
        img_feature = tf.io.parse_tensor(tfrecord_value['image_feature'], 'float32')

        if imf_norm_op:
            img_feature = tf.math.l2_normalize(img_feature)

        slide_labels = tfrecord_value['label']
        slide_label = int(slide_labels)

        image_features.append(img_feature)

    return image_features, slide_label


def most_frequent(List):
    mf = max(set(List), key=List.count)
    return mf


def tf_shut_up(no_warn_op=False):
    if no_warn_op:
        tf.get_logger().setLevel('ERROR')
    else:
        print('Are you sure you want to receive the annoying TensorFlow Warning Messages?', \
              '\n', 'If not, check the value of your input prameter for this function and re-run it.')


def optimizer_func_options(weight_decay_op_name):

    str_bool_dic = str_to_bool()
    weight_decay_op = str_bool_dic[weight_decay_op_name]

    wd_keys = ["AdamW", "SGDW", "LAMB", "NovoGrad", "RectifiedAdam"]
    nwd_keys = ["ConditionalGradient", "LazyAdam", "ProximalAdagrad", "Yogi", "Adam",
                "Adadelta", "Adagrad", "Adamax", "Ftrl", "Nadam", "RMSprop", "SGD"]

    optimizer_func_dic = {"AdamW": tfa.optimizers.AdamW,
                          "SGDW": tfa.optimizers.SGDW,
                          "LAMB": tfa.optimizers.LAMB,
                          "NovoGrad": tfa.optimizers.NovoGrad,
                          "RectifiedAdam": tfa.optimizers.RectifiedAdam,
                          "ConditionalGradient": tfa.optimizers.ConditionalGradient,
                          "LazyAdam": tfa.optimizers.LazyAdam,
                          "ProximalAdagrad": tfa.optimizers.ProximalAdagrad,
                          "Yogi": tfa.optimizers.Yogi,
                          "Adam": tf.keras.optimizers.Adam,
                          "Adadelta": tf.keras.optimizers.Adadelta,
                          "Adagrad": tf.keras.optimizers.Adagrad,
                          "Adamax": tf.keras.optimizers.Adamax,
                          "Ftrl": tf.keras.optimizers.Ftrl,
                          "Nadam": tf.keras.optimizers.Nadam,
                          "RMSprop": tf.keras.optimizers.RMSprop,
                          "SGD": tf.keras.optimizers.SGD}

    if weight_decay_op:
        [optimizer_func_dic.pop(key) for key in nwd_keys]
    else:
        [optimizer_func_dic.pop(key) for key in wd_keys]

    return optimizer_func_dic

def loss_func_options():
    loss_func_dic = {"binary_crossentropy": tf.keras.losses.binary_crossentropy,
                     "hinge": tf.keras.losses.hinge,
                     "categorical_crossentropy": tf.keras.losses.categorical_crossentropy,
                     "categorical_hinge": tf.keras.losses.categorical_hinge,
                     "cosine_similarity": tf.keras.losses.cosine_similarity,
                     "huber": tf.keras.losses.huber,
                     "log_cosh": tf.keras.losses.log_cosh,
                     "poisson": tf.keras.losses.poisson,
                     "squared_hinge": tf.keras.losses.squared_hinge,
                     "contrastive": tfa.losses.contrastive_loss,
                     "pinball": tfa.losses.pinball_loss,
                     "sigmoid_focal_crossentropy": tfa.losses.sigmoid_focal_crossentropy}

    return loss_func_dic

def load_optimizers(i_wd_op_name, b_wd_op_name, a_wd_op_name,
                    i_optimizer_name, b_optimizer_name, a_optimizer_name,
                    i_learn_rate, b_learn_rate, a_learn_rate,
                    i_l2_decay, b_l2_decay, a_l2_decay):

    str_bool_dic = str_to_bool()

    i_wd_op = str_bool_dic[i_wd_op_name]
    b_wd_op = str_bool_dic[b_wd_op_name]
    a_wd_op = str_bool_dic[a_wd_op_name]

    i_tf_func_dic = optimizer_func_options(weight_decay_op_name=i_wd_op_name)
    b_tf_func_dic = optimizer_func_options(weight_decay_op_name=b_wd_op_name)
    c_tf_func_dic = optimizer_func_options(weight_decay_op_name=a_wd_op_name)

    i_optimizer_func = i_tf_func_dic[i_optimizer_name]
    b_optimizer_func = b_tf_func_dic[b_optimizer_name]
    c_optimizer_func = c_tf_func_dic[a_optimizer_name]

    if i_wd_op:
        if i_optimizer_name == 'LAMB':
            i_optimizer = i_optimizer_func(learning_rate=i_learn_rate, weight_decay_rate=i_l2_decay)
        else:
            i_optimizer = i_optimizer_func(learning_rate=i_learn_rate, weight_decay=i_l2_decay)
    else:
        i_optimizer = i_optimizer_func(learning_rate=i_learn_rate)

    if b_wd_op:
        if b_optimizer_name == 'LAMB':
            b_optimizer = b_optimizer_func(learning_rate=b_learn_rate, weight_decay_rate=b_l2_decay)
        else:
            b_optimizer = b_optimizer_func(learning_rate=b_learn_rate, weight_decay=b_l2_decay)
    else:
        b_optimizer = b_optimizer_func(learning_rate=b_learn_rate)

    if a_wd_op:
        if a_optimizer_name == 'LAMB':
            c_optimizer = c_optimizer_func(learning_rate=a_learn_rate, weight_decay_rate=a_l2_decay)
        else:
            c_optimizer = c_optimizer_func(learning_rate=a_learn_rate, weight_decay=a_l2_decay)
    else:
        c_optimizer = c_optimizer_func(learning_rate=a_learn_rate)

    return i_optimizer, b_optimizer, c_optimizer


def load_loss_func(i_loss_func_name, b_loss_func_name):

    tf_func_dic = loss_func_options()

    i_loss_func = tf_func_dic[i_loss_func_name]
    b_loss_func = tf_func_dic[b_loss_func_name]

    return i_loss_func, b_loss_func

def str_to_bool():
    str_bool_dic = {'True': True,
                    'False': False}

    return str_bool_dic

def dataset_shuffle(dataset, path, percent):
    """
    Input Arg:
        dataset -> path where all tfrecord data stored
        path -> path where you want to save training, testing, and validation data folder
    """

    # return training, validation, and testing path name
    train = path + '/train'
    valid = path + '/valid'
    test = path + '/test'

    # create training, validation, and testing directory only if it is not existed
    if not os.path.exists(train):
        os.mkdir(os.path.join(path, 'train'))

    if not os.path.exists(valid):
        os.mkdir(os.path.join(path, 'valid'))

    if not os.path.exists(test):
        os.mkdir(os.path.join(path, 'test'))

    total_num_data = len(os.listdir(dataset))

    # only shuffle the data when train, validation, and test directory are all empty
    if len(os.listdir(train)) == 0 & len(os.listdir(valid)) == 0 & len(os.listdir(test)) == 0:
        train_names = random.sample(os.listdir(dataset), int(total_num_data * percent[0]))
        for i in train_names:
            train_srcpath = os.path.join(dataset, i)
            shutil.copy(train_srcpath, train)

        valid_names = random.sample(list(set(os.listdir(dataset)) - set(os.listdir(train))),
                                    int(total_num_data * percent[1]))
        for j in valid_names:
            valid_srcpath = os.path.join(dataset, j)
            shutil.copy(valid_srcpath, valid)

        test_names = list(set(os.listdir(dataset)) - set(os.listdir(train)) - set(os.listdir(valid)))
        for k in test_names:
            test_srcpath = os.path.join(dataset, k)
            shutil.copy(test_srcpath, test)

def ng_att_call(ng_att_net, img_features):
    h = list()
    A = list()

    for i in img_features:
        c_imf = ng_att_net[0](i)
        h.append(c_imf)

    for j in h:
        a = ng_att_net[1](j)
        A.append(a)
    return h, A


def g_att_call(g_att_net, img_features):
    h = list()
    A = list()

    for i in img_features:
        c_imf = g_att_net[0](i)
        h.append(c_imf)

    for j in h:
        att_v_output = g_att_net[1](j)
        att_u_output = g_att_net[2](j)
        att_input = tf.math.multiply(att_v_output, att_u_output)
        a = g_att_net[3](att_input)
        A.append(a)

    return h, A


def generate_pos_labels(n_pos_sample):
    return tf.fill(dims=[n_pos_sample, ], value=1)


def generate_neg_labels(n_neg_sample):
    return tf.fill(dims=[n_neg_sample, ], value=0)


def ins_in_call(ins_classifier, h, A_I, top_k_percent, n_class):
    n_ins = top_k_percent * len(h)
    n_ins = int(n_ins)

    pos_label = generate_pos_labels(n_pos_sample=n_ins)
    neg_label = generate_neg_labels(n_neg_sample=n_ins)
    ins_label_in = tf.concat(values=[pos_label, neg_label], axis=0)

    A_I = tf.reshape(tf.convert_to_tensor(A_I), (1, len(A_I)))

    top_pos_ids = tf.math.top_k(A_I, n_ins)[1][-1]
    pos_index = list()
    for i in top_pos_ids:
        pos_index.append(i)

    pos_index = tf.convert_to_tensor(pos_index)
    top_pos = list()
    for i in pos_index:
        top_pos.append(h[i])

    top_neg_ids = tf.math.top_k(-A_I, n_ins)[1][-1]
    neg_index = list()
    for i in top_neg_ids:
        neg_index.append(i)

    neg_index = tf.convert_to_tensor(neg_index)
    top_neg = list()
    for i in neg_index:
        top_neg.append(h[i])

    ins_in = tf.concat(values=[top_pos, top_neg], axis=0)
    logits_unnorm_in = list()
    logits_in = list()

    for i in range(n_class * n_ins):
        ins_score_unnorm_in = ins_classifier(ins_in[i])
        logit_in = tf.math.softmax(ins_score_unnorm_in)
        logits_unnorm_in.append(ins_score_unnorm_in)
        logits_in.append(logit_in)

    return ins_label_in, logits_unnorm_in, logits_in


def ins_out_call(ins_classifier, h, A_O, top_k_percent):
    n_ins = top_k_percent * len(h)
    n_ins = int(n_ins)

    # get compressed 512-dimensional instance-level feature vectors for following use, denoted by h
    A_O = tf.reshape(tf.convert_to_tensor(A_O), (1, len(A_O)))

    top_pos_ids = tf.math.top_k(A_O, n_ins)[1][-1]
    pos_index = list()
    for i in top_pos_ids:
        pos_index.append(i)

    pos_index = tf.convert_to_tensor(pos_index)
    top_pos = list()
    for i in pos_index:
        top_pos.append(h[i])

    # mutually-exclusive -> top k instances w/ highest attention scores ==> false pos = neg
    pos_ins_labels_out = generate_neg_labels(n_neg_sample=n_ins)
    ins_label_out = pos_ins_labels_out

    logits_unnorm_out = list()
    logits_out = list()

    for i in range(n_ins):
        ins_score_unnorm_out = ins_classifier(top_pos[i])
        logit_out = tf.math.softmax(ins_score_unnorm_out)
        logits_unnorm_out.append(ins_score_unnorm_out)
        logits_out.append(logit_out)

    return ins_label_out, logits_unnorm_out, logits_out


def ins_call(m_ins_classifier, bag_label, h, A, n_class, top_k_percent, mut_ex):
    for i in range(n_class):
        ins_classifier = m_ins_classifier[i]
        if i == bag_label:
            A_I = list()
            for j in range(len(A)):
                a_i = A[j][0][i]
                A_I.append(a_i)
            ins_label_in, logits_unnorm_in, logits_in = ins_in_call(ins_classifier=ins_classifier,
                                                                    h=h, A_I=A_I,
                                                                    top_k_percent=top_k_percent,
                                                                    n_class=n_class)
        else:
            if mut_ex:
                A_O = list()
                for j in range(len(A)):
                    a_o = A[j][0][i]
                    A_O.append(a_o)
                ins_label_out, logits_unnorm_out, logits_out = ins_out_call(ins_classifier=ins_classifier,
                                                                            h=h, A_O=A_O,
                                                                            top_k_percent=top_k_percent)
            else:
                continue

    if mut_ex:
        ins_labels = tf.concat(values=[ins_label_in, ins_label_out], axis=0)
        ins_logits_unnorm = logits_unnorm_in + logits_unnorm_out
        ins_logits = logits_in + logits_out
    else:
        ins_labels = ins_label_in
        ins_logits_unnorm = logits_unnorm_in
        ins_logits = logits_in

    return ins_labels, ins_logits_unnorm, ins_logits

def s_bag_h_slide(A, h):
    # compute the slide-level representation aggregated per the attention score distribution for the mth class
    SAR = list()
    for i in range(len(A)):
        sar = tf.linalg.matmul(tf.transpose(A[i]), h[i])  # shape be (2,512)
        SAR.append(sar)

    slide_agg_rep = tf.math.add_n(SAR)  # return h_[slide,m], shape be (2,512)

    return slide_agg_rep


def s_bag_call(bag_classifier, bag_label, A, h, n_class):
    slide_agg_rep = s_bag_h_slide(A=A, h=h)

    slide_score_unnorm = bag_classifier(slide_agg_rep)
    slide_score_unnorm = tf.reshape(slide_score_unnorm, (1, n_class))

    Y_hat = tf.math.top_k(slide_score_unnorm, 1)[1][-1]

    Y_prob = tf.math.softmax(tf.reshape(slide_score_unnorm,
                             (1, n_class)))  # shape be (1,2), predictions for each of the classes

    predict_slide_label = np.argmax(Y_prob.numpy())

    Y_true = tf.one_hot([bag_label], 2)

    return slide_score_unnorm, Y_hat, Y_prob, predict_slide_label, Y_true

def m_bag_h_slide(A, h, dim_compress_features, n_class):
    SAR = list()
    for i in range(len(A)):
        sar = tf.linalg.matmul(tf.transpose(A[i]), h[i])  # shape be (2,512)
        SAR.append(sar)

    SAR_Branch = list()
    for i in range(n_class):
        sar_branch = list()
        for j in range(len(SAR)):
            sar_c = tf.reshape(SAR[j][i], (1, dim_compress_features))
            sar_branch.append(sar_c)
        SAR_Branch.append(sar_branch)

    slide_agg_rep = list()
    for k in range(n_class):
        slide_agg_rep.append(tf.math.add_n(SAR_Branch[k]))

    return slide_agg_rep

def m_bag_call(m_bag_classifier, bag_label, A, h, n_class, dim_compress_features):
    slide_agg_rep = m_bag_h_slide(A=A, h=h, dim_compress_features=dim_compress_features, n_class=n_class)

    ssus = list()
    # return s_[slide,m] (slide-level prediction scores)
    for i in range(n_class):
        bag_classifier = m_bag_classifier[i]
        ssu = bag_classifier(slide_agg_rep[i])
        ssus.append(ssu[0][0])

    slide_score_unnorm = tf.convert_to_tensor(ssus)
    slide_score_unnorm = tf.reshape(slide_score_unnorm, (1, n_class))

    Y_hat = tf.math.top_k(slide_score_unnorm, 1)[1][-1]
    Y_prob = tf.math.softmax(slide_score_unnorm)
    predict_slide_label = np.argmax(Y_prob.numpy())

    Y_true = tf.one_hot([bag_label], 2)

    return slide_score_unnorm, Y_hat, Y_prob, predict_slide_label, Y_true

def s_clam_call(att_net, ins_net, bag_net, img_features, slide_label,
                n_class, top_k_percent, att_gate, att_only, mil_ins, mut_ex):
    if att_gate:
        h, A = g_att_call(g_att_net=att_net, img_features=img_features)
    else:
        h, A = ng_att_call(ng_att_net=att_net, img_features=img_features)
    att_score = A  # output from attention network
    A = tf.math.softmax(A)   # softmax on attention scores

    if att_only:
        return att_score

    if mil_ins:
        ins_labels, ins_logits_unnorm, ins_logits = ins_call(m_ins_classifier=ins_net,
                                                             bag_label=slide_label,
                                                             h=h, A=A,
                                                             n_class=n_class,
                                                             top_k_percent=top_k_percent,
                                                             mut_ex=mut_ex)

    slide_score_unnorm, Y_hat, Y_prob, predict_slide_label, Y_true = s_bag_call(bag_classifier=bag_net,
                                                                                bag_label=slide_label,
                                                                                A=A, h=h, n_class=n_class)

    return att_score, A, h, ins_labels, ins_logits_unnorm, ins_logits, \
           slide_score_unnorm, Y_prob, Y_hat, Y_true, predict_slide_label

def m_clam_call(att_net, ins_net, bag_net, img_features, slide_label,
                n_class, dim_compress_features, top_k_percent, att_gate, att_only, mil_ins, mut_ex):
    if att_gate:
        h, A = g_att_call(g_att_net=att_net, img_features=img_features)
    else:
        h, A = ng_att_call(ng_att_net=att_net, img_features=img_features)
    att_score = A  # output from attention network
    A = tf.math.softmax(A)  # softmax on attention scores

    if att_only:
        return att_score

    if mil_ins:
        ins_labels, ins_logits_unnorm, ins_logits = ins_call(m_ins_classifier=ins_net,
                                                             bag_label=slide_label,
                                                             h=h, A=A,
                                                             n_class=n_class,
                                                             top_k_percent=top_k_percent,
                                                             mut_ex=mut_ex)

    slide_score_unnorm, Y_hat, Y_prob, \
    predict_slide_label, Y_true = m_bag_call(m_bag_classifier=bag_net, bag_label=slide_label,
                                             A=A, h=h, n_class=n_class,
                                             dim_compress_features=dim_compress_features)

    return att_score, A, h, ins_labels, ins_logits_unnorm, ins_logits, \
           slide_score_unnorm, Y_prob, Y_hat, Y_true, predict_slide_label

def model_save(c_model, c_model_dir, n_class, m_clam_op, att_gate):

    clam_model_names = ['_Att', '_Ins', '_Bag']

    if m_clam_op:
        if att_gate:
            att_nets = c_model.clam_model()[0]
            for m in range(len(att_nets)):
                att_nets[m].save(os.path.join(c_model_dir, 'G' + clam_model_names[0], 'Model_' + str(m + 1)))
        else:
            att_nets = c_model.clam_model()[0]
            for m in range(len(att_nets)):
                att_nets[m].save(os.path.join(c_model_dir, 'NG' + clam_model_names[0], 'Model_' + str(m + 1)))

        for n in range(n_class):
            ins_nets = c_model.clam_model()[1]
            bag_nets = c_model.clam_model()[2]

            ins_nets[n].save(os.path.join(c_model_dir, 'M' + clam_model_names[1], 'Class_' + str(n)))
            bag_nets[n].save(os.path.join(c_model_dir, 'M' + clam_model_names[2], 'Class_' + str(n)))
    else:
        if att_gate:
            att_nets = c_model.clam_model()[0]
            for m in range(len(att_nets)):
                att_nets[m].save(os.path.join(c_model_dir, 'G' + clam_model_names[0], 'Model_' + str(m + 1)))
        else:
            att_nets = c_model.clam_model()[0]
            for m in range(len(att_nets)):
                att_nets[m].save(os.path.join(c_model_dir, 'NG' + clam_model_names[0], 'Model_' + str(m + 1)))

        for n in range(n_class):
            ins_nets = c_model.clam_model()[1]
            ins_nets[n].save(os.path.join(c_model_dir, 'M' + clam_model_names[1], 'Class_' + str(n)))

        c_model.clam_model()[2].save(os.path.join(c_model_dir, 'S' + clam_model_names[2]))


def restore_model(c_model_dir, n_class, m_clam_op, att_gate):

    clam_model_names = ['_Att', '_Ins', '_Bag']

    trained_att_net = list()
    trained_ins_classifier = list()
    trained_bag_classifier = list()

    if m_clam_op:
        if att_gate:
            att_nets_dir = os.path.join(c_model_dir, 'G' + clam_model_names[0])
            for k in range(len(os.listdir(att_nets_dir))):
                att_net = tf.keras.models.load_model(os.path.join(att_nets_dir, 'Model_' + str(k + 1)))
                trained_att_net.append(att_net)
        else:
            att_nets_dir = os.path.join(c_model_dir, 'NG' + clam_model_names[0])
            for k in range(len(os.listdir(att_nets_dir))):
                att_net = tf.keras.models.load_model(os.path.join(att_nets_dir, 'Model_' + str(k + 1)))
                trained_att_net.append(att_net)

        ins_nets_dir = os.path.join(c_model_dir, 'M' + clam_model_names[1])
        bag_nets_dir = os.path.join(c_model_dir, 'M' + clam_model_names[2])

        for m in range(n_class):
            ins_net = tf.keras.models.load_model(os.path.join(ins_nets_dir, 'Class_' + str(m)))
            bag_net = tf.keras.models.load_model(os.path.join(bag_nets_dir, 'Class_' + str(m)))

            trained_ins_classifier.append(ins_net)
            trained_bag_classifier.append(bag_net)

        c_trained_model = [trained_att_net, trained_ins_classifier, trained_bag_classifier]
    else:
        if att_gate:
            att_nets_dir = os.path.join(c_model_dir, 'G' + clam_model_names[0])
            for k in range(len(os.listdir(att_nets_dir))):
                att_net = tf.keras.models.load_model(os.path.join(att_nets_dir, 'Model_' + str(k + 1)))
                trained_att_net.append(att_net)
        else:
            att_nets_dir = os.path.join(c_model_dir, 'NG' + clam_model_names[0])
            for k in range(len(os.listdir(att_nets_dir))):
                att_net = tf.keras.models.load_model(os.path.join(att_nets_dir, 'Model_' + str(k + 1)))
                trained_att_net.append(att_net)

        ins_nets_dir = os.path.join(c_model_dir, 'M' + clam_model_names[1])

        for m in range(n_class):
            ins_net = tf.keras.models.load_model(os.path.join(ins_nets_dir, 'Class_' + str(m)))
            trained_ins_classifier.append(ins_net)

        bag_nets_dir = os.path.join(c_model_dir, 'S' + clam_model_names[2])
        trained_bag_classifier.append(tf.keras.models.load_model(bag_nets_dir))

        c_trained_model = [trained_att_net, trained_ins_classifier, trained_bag_classifier[0]]

    return c_trained_model