package com.paycheck.paycheckanalyzerapi.dashboard.dto;

import java.math.BigDecimal;
import java.time.LocalDate;
import java.util.List;
import java.util.Map;

public class DashboardSummaryDto {

    private String month;
    private BigDecimal totalSpending;
    private BigDecimal averageDaily;
    private List<CategorySummary> categories;
    private List<DailySpending> dailySpending;
    private List<CumulativePoint> cumulative;
    private List<TopPurchase> topPurchases;
    private List<ProductItem> products;

    public static class CategorySummary {
        private Long categoryId;
        private String categoryName;
        private String color;
        private BigDecimal total;
        private double percentage;

        public Long getCategoryId() {
            return categoryId;
        }

        public void setCategoryId(Long categoryId) {
            this.categoryId = categoryId;
        }

        public String getCategoryName() {
            return categoryName;
        }

        public void setCategoryName(String categoryName) {
            this.categoryName = categoryName;
        }

        public String getColor() {
            return color;
        }

        public void setColor(String color) {
            this.color = color;
        }

        public BigDecimal getTotal() {
            return total;
        }

        public void setTotal(BigDecimal total) {
            this.total = total;
        }

        public double getPercentage() {
            return percentage;
        }

        public void setPercentage(double percentage) {
            this.percentage = percentage;
        }
    }

    public static class DailySpending {
        private LocalDate date;
        private BigDecimal total;
        private boolean isOutlier;

        public LocalDate getDate() {
            return date;
        }

        public void setDate(LocalDate date) {
            this.date = date;
        }

        public BigDecimal getTotal() {
            return total;
        }

        public void setTotal(BigDecimal total) {
            this.total = total;
        }

        public boolean isOutlier() {
            return isOutlier;
        }

        public void setOutlier(boolean outlier) {
            isOutlier = outlier;
        }
    }

    public static class CumulativePoint {
        private LocalDate date;
        private Map<String, BigDecimal> categories;

        public LocalDate getDate() {
            return date;
        }

        public void setDate(LocalDate date) {
            this.date = date;
        }

        public Map<String, BigDecimal> getCategories() {
            return categories;
        }

        public void setCategories(Map<String, BigDecimal> categories) {
            this.categories = categories;
        }
    }

    public static class TopPurchase {
        private Long id;
        private String productName;
        private BigDecimal amount;
        private String categoryName;
        private LocalDate date;

        public Long getId() {
            return id;
        }

        public void setId(Long id) {
            this.id = id;
        }

        public String getProductName() {
            return productName;
        }

        public void setProductName(String productName) {
            this.productName = productName;
        }

        public BigDecimal getAmount() {
            return amount;
        }

        public void setAmount(BigDecimal amount) {
            this.amount = amount;
        }

        public String getCategoryName() {
            return categoryName;
        }

        public void setCategoryName(String categoryName) {
            this.categoryName = categoryName;
        }

        public LocalDate getDate() {
            return date;
        }

        public void setDate(LocalDate date) {
            this.date = date;
        }
    }

    public static class ProductItem {
        private Long id;
        private String name;

        public Long getId() {
            return id;
        }

        public void setId(Long id) {
            this.id = id;
        }

        public String getName() {
            return name;
        }

        public void setName(String name) {
            this.name = name;
        }
    }

    public String getMonth() {
        return month;
    }

    public void setMonth(String month) {
        this.month = month;
    }

    public BigDecimal getTotalSpending() {
        return totalSpending;
    }

    public void setTotalSpending(BigDecimal totalSpending) {
        this.totalSpending = totalSpending;
    }

    public BigDecimal getAverageDaily() {
        return averageDaily;
    }

    public void setAverageDaily(BigDecimal averageDaily) {
        this.averageDaily = averageDaily;
    }

    public List<CategorySummary> getCategories() {
        return categories;
    }

    public void setCategories(List<CategorySummary> categories) {
        this.categories = categories;
    }

    public List<DailySpending> getDailySpending() {
        return dailySpending;
    }

    public void setDailySpending(List<DailySpending> dailySpending) {
        this.dailySpending = dailySpending;
    }

    public List<CumulativePoint> getCumulative() {
        return cumulative;
    }

    public void setCumulative(List<CumulativePoint> cumulative) {
        this.cumulative = cumulative;
    }

    public List<TopPurchase> getTopPurchases() {
        return topPurchases;
    }

    public void setTopPurchases(List<TopPurchase> topPurchases) {
        this.topPurchases = topPurchases;
    }

    public List<ProductItem> getProducts() {
        return products;
    }

    public void setProducts(List<ProductItem> products) {
        this.products = products;
    }
}

