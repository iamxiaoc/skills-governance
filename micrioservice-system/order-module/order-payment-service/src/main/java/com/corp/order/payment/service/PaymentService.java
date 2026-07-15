package com.corp.order.payment.service;

import java.util.Map;

/**
 * 支付Service接口
 */
public interface PaymentService {

    Map<String, String> createPayment(Map<String, Object> paymentMap);

    Map<String, Object> getPaymentStatus(String paymentId);

    boolean refund(String paymentId, Map<String, Object> refundMap);
}
