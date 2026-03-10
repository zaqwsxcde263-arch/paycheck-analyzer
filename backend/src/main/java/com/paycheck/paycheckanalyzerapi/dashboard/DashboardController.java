package com.paycheck.paycheckanalyzerapi.dashboard;

import com.paycheck.paycheckanalyzerapi.dashboard.dto.DashboardSummaryDto;
import com.paycheck.paycheckanalyzerapi.dashboard.dto.ProductHistoryDto;
import com.paycheck.paycheckanalyzerapi.user.User;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RequestParam;
import org.springframework.web.bind.annotation.RestController;

@RestController
@RequestMapping("/api/v1/dashboard")
public class DashboardController {

    private final DashboardService dashboardService;

    public DashboardController(DashboardService dashboardService) {
        this.dashboardService = dashboardService;
    }

    @GetMapping("/summary")
    public ResponseEntity<DashboardSummaryDto> getSummary(
            @AuthenticationPrincipal User user,
            @RequestParam(required = false) String month) {
        DashboardSummaryDto summary = dashboardService.getMonthlySummary(user, month);
        return ResponseEntity.ok(summary);
    }

    @GetMapping("/product-history")
    public ResponseEntity<ProductHistoryDto> getProductHistory(
            @AuthenticationPrincipal User user,
            @RequestParam("productId") Long productId,
            @RequestParam(value = "months", required = false) Integer months) {
        ProductHistoryDto history = dashboardService.getProductHistory(user, productId, months);
        return ResponseEntity.ok(history);
    }
}

