package com.paycheck.paycheckanalyzerapi.dashboard;

import com.paycheck.paycheckanalyzerapi.dashboard.dto.DashboardSummaryDto;
import com.paycheck.paycheckanalyzerapi.dashboard.dto.ProductHistoryDto;
import com.paycheck.paycheckanalyzerapi.spending.Spending;
import com.paycheck.paycheckanalyzerapi.spending.SpendingRepository;
import com.paycheck.paycheckanalyzerapi.user.User;
import java.math.BigDecimal;
import java.math.RoundingMode;
import java.time.LocalDate;
import java.time.YearMonth;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Set;
import java.util.stream.Collectors;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

@Service
public class DashboardService {

    private final SpendingRepository spendingRepository;

    public DashboardService(SpendingRepository spendingRepository) {
        this.spendingRepository = spendingRepository;
    }

    @Transactional(readOnly = true)
    public DashboardSummaryDto getMonthlySummary(User user, String monthParam) {
        YearMonth ym = (monthParam != null && !monthParam.isEmpty())
                ? YearMonth.parse(monthParam)
                : YearMonth.now();
        LocalDate from = ym.atDay(1);
        LocalDate to = ym.atEndOfMonth();

        List<Spending> monthSpendings =
                spendingRepository.findByUserAndDateBetweenOrderByDateAsc(user, from, to);

        BigDecimal total = monthSpendings.stream()
                .map(Spending::getAmount)
                .reduce(BigDecimal.ZERO, BigDecimal::add);

        int daysInMonth = ym.lengthOfMonth();
        BigDecimal averageDaily = daysInMonth > 0
                ? total.divide(BigDecimal.valueOf(daysInMonth), 2, RoundingMode.HALF_UP)
                : BigDecimal.ZERO;

        Map<Long, BigDecimal> byCategory = new HashMap<>();
        Map<Long, String> categoryNames = new HashMap<>();
        Map<Long, String> categoryColors = new HashMap<>();

        for (Spending s : monthSpendings) {
            Long categoryId = s.getCategory().getId();
            byCategory.merge(categoryId, s.getAmount(), BigDecimal::add);
            categoryNames.putIfAbsent(categoryId, s.getCategory().getName());
            categoryColors.putIfAbsent(categoryId, s.getCategory().getColor());
        }

        List<DashboardSummaryDto.CategorySummary> categorySummaries = new ArrayList<>();
        for (Map.Entry<Long, BigDecimal> entry : byCategory.entrySet()) {
            DashboardSummaryDto.CategorySummary cs = new DashboardSummaryDto.CategorySummary();
            cs.setCategoryId(entry.getKey());
            cs.setCategoryName(categoryNames.get(entry.getKey()));
            cs.setColor(categoryColors.get(entry.getKey()));
            cs.setTotal(entry.getValue());
            if (total.compareTo(BigDecimal.ZERO) > 0) {
                double pct = entry.getValue()
                        .multiply(BigDecimal.valueOf(100))
                        .divide(total, 2, RoundingMode.HALF_UP)
                        .doubleValue();
                cs.setPercentage(pct);
            } else {
                cs.setPercentage(0.0);
            }
            categorySummaries.add(cs);
        }

        Map<LocalDate, BigDecimal> totalsByDate = new LinkedHashMap<>();
        for (Spending s : monthSpendings) {
            totalsByDate.merge(s.getDate(), s.getAmount(), BigDecimal::add);
        }

        BigDecimal threshold = averageDaily.multiply(BigDecimal.valueOf(1.5));
        List<DashboardSummaryDto.DailySpending> dailySpending = new ArrayList<>();
        for (Map.Entry<LocalDate, BigDecimal> entry : totalsByDate.entrySet()) {
            DashboardSummaryDto.DailySpending ds = new DashboardSummaryDto.DailySpending();
            ds.setDate(entry.getKey());
            ds.setTotal(entry.getValue());
            ds.setOutlier(entry.getValue().compareTo(threshold) > 0);
            dailySpending.add(ds);
        }

        Map<LocalDate, Map<Long, BigDecimal>> cumulativeByDate = new LinkedHashMap<>();
        for (Spending s : monthSpendings) {
            LocalDate date = s.getDate();
            cumulativeByDate.computeIfAbsent(date, d -> new HashMap<>());
            Map<Long, BigDecimal> mapForDate = cumulativeByDate.get(date);
            mapForDate.merge(s.getCategory().getId(), s.getAmount(), BigDecimal::add);
        }

        Map<Long, BigDecimal> runningTotals = new HashMap<>();
        List<DashboardSummaryDto.CumulativePoint> cumulativePoints = new ArrayList<>();
        List<LocalDate> sortedDates = new ArrayList<>(cumulativeByDate.keySet());
        sortedDates.sort(Comparator.naturalOrder());

        for (LocalDate date : sortedDates) {
            Map<Long, BigDecimal> dayMap = cumulativeByDate.get(date);
            for (Map.Entry<Long, BigDecimal> entry : dayMap.entrySet()) {
                runningTotals.merge(entry.getKey(), entry.getValue(), BigDecimal::add);
            }
            DashboardSummaryDto.CumulativePoint cp = new DashboardSummaryDto.CumulativePoint();
            cp.setDate(date);
            Map<String, BigDecimal> categories = new LinkedHashMap<>();
            for (Map.Entry<Long, BigDecimal> entry : runningTotals.entrySet()) {
                categories.put(entry.getKey().toString(), entry.getValue());
            }
            cp.setCategories(categories);
            cumulativePoints.add(cp);
        }

        List<Spending> topPurchasesEntities =
                spendingRepository.findTop10ByUserAndDateBetweenOrderByAmountDesc(user, from, to);
        List<DashboardSummaryDto.TopPurchase> topPurchases = topPurchasesEntities.stream()
                .map(s -> {
                    DashboardSummaryDto.TopPurchase tp = new DashboardSummaryDto.TopPurchase();
                    tp.setId(s.getId());
                    tp.setProductName(s.getProductName());
                    tp.setAmount(s.getAmount());
                    tp.setCategoryName(s.getCategory().getName());
                    tp.setDate(s.getDate());
                    return tp;
                })
                .collect(Collectors.toList());

        Set<Long> productIds = monthSpendings.stream()
                .map(Spending::getId)
                .collect(Collectors.toSet());
        List<DashboardSummaryDto.ProductItem> products = monthSpendings.stream()
                .filter(s -> productIds.contains(s.getId()))
                .map(s -> {
                    DashboardSummaryDto.ProductItem p = new DashboardSummaryDto.ProductItem();
                    p.setId(s.getId());
                    p.setName(s.getProductName());
                    return p;
                })
                .collect(Collectors.toMap(
                        DashboardSummaryDto.ProductItem::getId,
                        p -> p,
                        (a, b) -> a,
                        LinkedHashMap::new))
                .values()
                .stream()
                .collect(Collectors.toList());

        DashboardSummaryDto dto = new DashboardSummaryDto();
        dto.setMonth(ym.toString());
        dto.setTotalSpending(total);
        dto.setAverageDaily(averageDaily);
        dto.setCategories(categorySummaries);
        dto.setDailySpending(dailySpending);
        dto.setCumulative(cumulativePoints);
        dto.setTopPurchases(topPurchases);
        dto.setProducts(products);
        return dto;
    }

    @Transactional(readOnly = true)
    public ProductHistoryDto getProductHistory(User user, Long productId, Integer months) {
        int rangeMonths = (months == null || months <= 0) ? 6 : months;

        Spending reference = spendingRepository.findByIdAndUser(productId, user)
                .orElseThrow(() -> new IllegalArgumentException("Spending not found"));

        LocalDate end = LocalDate.now();
        LocalDate start = end.minusMonths(rangeMonths);

        List<Spending> historyEntities =
                spendingRepository.findByUserAndProductNameAndDateBetweenOrderByDateAsc(
                        user, reference.getProductName(), start, end);

        ProductHistoryDto dto = new ProductHistoryDto();
        dto.setProductName(reference.getProductName());
        List<ProductHistoryDto.Point> history = historyEntities.stream()
                .map(s -> {
                    ProductHistoryDto.Point p = new ProductHistoryDto.Point();
                    p.setDate(s.getDate());
                    p.setAmount(s.getAmount());
                    return p;
                })
                .collect(Collectors.toList());
        dto.setHistory(history);
        return dto;
    }
}

