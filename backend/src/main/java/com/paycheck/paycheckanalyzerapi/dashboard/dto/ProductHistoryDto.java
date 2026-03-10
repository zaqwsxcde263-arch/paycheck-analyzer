package com.paycheck.paycheckanalyzerapi.dashboard.dto;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;

public class ProductHistoryDto {

    private String productName;
    private List<Point> history;

    public static class Point {
        private LocalDate date;
        private BigDecimal amount;

        public LocalDate getDate() {
            return date;
        }

        public void setDate(LocalDate date) {
            this.date = date;
        }

        public BigDecimal getAmount() {
            return amount;
        }

        public void setAmount(BigDecimal amount) {
            this.amount = amount;
        }
    }

    public String getProductName() {
        return productName;
    }

    public void setProductName(String productName) {
        this.productName = productName;
    }

    public List<Point> getHistory() {
        return history;
    }

    public void setHistory(List<Point> history) {
        this.history = history;
    }
}

