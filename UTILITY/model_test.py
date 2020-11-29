import pandas as pd
import sklearn
from sklearn import metrics
import os
import time

from UTILITY.util import get_data_from_tf, s_clam_call, ins_call, s_bag_call


def test_step(n_class, n_ins, att_gate, att_only, mil_ins, mut_ex, i_model, b_model, c_model,
              test_path, result_path, result_file_name):
    start_time = time.time()

    slide_true_label = list()
    slide_predict_label = list()
    sample_names = list()

    for i in os.listdir(test_path):
        print('>', end="")
        single_test_data = test_path + i
        img_features, slide_label = get_data_from_tf(single_test_data)

        att_score, A, h, ins_labels, ins_logits_unnorm, ins_logits, slide_score_unnorm, \
        Y_prob, Y_hat, Y_true, predict_slide_label = s_clam_call(att_net=c_model[0],
                                                                 ins_net=c_model[1],
                                                                 bag_net=c_model[2],
                                                                 img_features=img_features,
                                                                 slide_label=slide_label,
                                                                 n_class=n_class, n_ins=n_ins,
                                                                 att_gate=att_gate, att_only=att_only,
                                                                 mil_ins=mil_ins, mut_ex=mut_ex)

        ins_labels, ins_logits_unnorm, ins_logits = ins_call(m_ins_classifier=i_model,
                                                             bag_label=slide_label,
                                                             h=h, A=A, n_class=n_class,
                                                             n_ins=n_ins, mut_ex=mut_ex)

        slide_score_unnorm, Y_hat, Y_prob, predict_slide_label, Y_true = s_bag_call(bag_classifier=b_model,
                                                                                    bag_label=slide_label,
                                                                                    A=A, h=h, n_class=n_class)

        slide_true_label.append(slide_label)
        slide_predict_label.append(predict_slide_label)
        sample_names.append(i)

        test_results = pd.DataFrame(list(zip(sample_names, slide_true_label, slide_predict_label)),
                                    columns=['Sample Names', 'Slide True Label', 'Slide Predict Label'])
        test_results.to_csv(os.path.join(result_path, result_file_name), sep='\t', index=False)

    tn, fp, fn, tp = sklearn.metrics.confusion_matrix(slide_true_label, slide_predict_label).ravel()
    test_tn = int(tn)
    test_fp = int(fp)
    test_fn = int(fn)
    test_tp = int(tp)

    test_sensitivity = round(test_tp / (test_tp + test_fn), 2)
    test_specificity = round(test_tn / (test_tn + test_fp), 2)
    test_acc = round((test_tp + test_tn) / (test_tn + test_fp + test_fn + test_tp), 2)

    fpr, tpr, thresholds = sklearn.metrics.roc_curve(slide_true_label, slide_predict_label, pos_label=1)
    test_auc = round(sklearn.metrics.auc(fpr, tpr), 2)

    test_run_time = time.time() - start_time

    template = '\n Test Accuracy: {}, Test Sensitivity: {}, Test Specificity: {}, Test Running Time: {}'
    print(template.format(f"{float(test_acc):.4%}",
                          f"{float(test_sensitivity):.4%}",
                          f"{float(test_specificity):.4%}",
                          "--- %s mins ---" % int(test_run_time / 60)))