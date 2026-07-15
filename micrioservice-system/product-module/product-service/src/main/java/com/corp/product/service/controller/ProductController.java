package com.corp.product.service.controller;

import com.corp.base.common.result.Result;
import com.corp.product.service.service.ProductService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 商品Controller
 * 提供商品CRUD和搜索接口
 */
@RestController
@RequestMapping("/api/products")
public class ProductController {

    @Autowired
    private ProductService productService;

    @GetMapping("/{id}")
    public Result<Map<String, Object>> getProductById(@PathVariable Long id) {
        return Result.success(productService.getProductById(id));
    }

    @PostMapping
    public Result<Long> createProduct(@RequestBody Map<String, Object> productMap) {
        return Result.success(productService.createProduct(productMap));
    }

    @PutMapping("/{id}")
    public Result<Boolean> updateProduct(@PathVariable Long id, @RequestBody Map<String, Object> productMap) {
        return Result.success(productService.updateProduct(id, productMap));
    }

    @DeleteMapping("/{id}")
    public Result<Boolean> deleteProduct(@PathVariable Long id) {
        return Result.success(productService.deleteProduct(id));
    }

    @GetMapping("/search")
    public Result<List<Map<String, Object>>> searchProducts(@RequestParam String keyword,
                                                             @RequestParam(defaultValue = "1") int page,
                                                             @RequestParam(defaultValue = "10") int size) {
        return Result.success(productService.searchProducts(keyword, page, size));
    }
}
