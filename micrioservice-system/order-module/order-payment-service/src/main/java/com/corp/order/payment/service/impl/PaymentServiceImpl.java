package com.corp.order.payment.service.impl;

import com.corp.id.IdGenerator;
import com.corp.id.IdGeneratorFactory;
import com.corp.monitor.MonitorUtils;
import com.corp.order.payment.service.PaymentService;
import com.corp.trace.TraceUtils;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;

/**
 * PaymentService实现类
 */
@Service
public class PaymentServiceImpl implements PaymentService {

    private IdGenerator idGenerator = IdGeneratorFactory.getDefault();

    @Override
    public Map<String, String> createPayment(Map<String, Object> paymentMap) {
        // 简化版：实际应调用支付宝/微信支付SDK
        long startTime = MonitorUtils.startTimer();
        Map<String, String> result = new HashMap<>();
        String paymentId = idGenerator.nextBizId("PAY");
        result.put("paymentId", "PAY_" + paymentId);
        result.put("payUrl", "https://pay.example.com/pay?id=" + paymentId);
        MonitorUtils.increment("payment.create.count");
        MonitorUtils.stopTimer("payment.create.duration", startTime);
        return result;
    }

    @Override
    public Map<String, Object> getPaymentStatus(String paymentId) {
        // 简化版：实际应查询支付渠道
        Map<String, Object> result = new HashMap<>();
        result.put("paymentId", paymentId);
        result.put("status", "PAID");
        return result;
    }

    @Override
    public boolean refund(String paymentId, Map<String, Object> refundMap) {
        // 简化版：实际应调用支付渠道退款接口
        MonitorUtils.increment("payment.refund.count");
        return true;
    }
}
