package com.paycheck.paycheckanalyzerapi.spending.dto;

import com.paycheck.paycheckanalyzerapi.category.dto.CategoryDto;
import com.paycheck.paycheckanalyzerapi.spending.Spending;
import java.math.BigDecimal;
import java.time.LocalDate;

public class SpendingDto {

    private Long id;
    private String productName;
    private BigDecimal amount;
    private String seller;
    private LocalDate date;
    private CategoryDto category;
    private String notes;

    public static SpendingDto fromEntity(Spending spending) {
        SpendingDto dto = new SpendingDto();
        dto.setId(spending.getId());
        dto.setProductName(spending.getProductName());
        dto.setAmount(spending.getAmount());
        dto.setSeller(spending.getSeller());
        dto.setDate(spending.getDate());
        dto.setCategory(CategoryDto.fromEntity(spending.getCategory()));
        dto.setNotes(spending.getNotes());
        return dto;
    }

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

    public String getSeller() {
        return seller;
    }

    public void setSeller(String seller) {
        this.seller = seller;
    }

    public LocalDate getDate() {
        return date;
    }

    public void setDate(LocalDate date) {
        this.date = date;
    }

    public CategoryDto getCategory() {
        return category;
    }

    public void setCategory(CategoryDto category) {
        this.category = category;
    }

    public String getNotes() {
        return notes;
    }

    public void setNotes(String notes) {
        this.notes = notes;
    }
}

