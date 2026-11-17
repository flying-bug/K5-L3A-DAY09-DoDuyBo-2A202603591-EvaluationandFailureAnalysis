# Judge audit

Chạy: `python -m lab9.judge --csv <file> --audit 5` (thư mục `src/`, judge REPLAY, không cần API key). Lớp dương = `FAIL`, vì việc của judge là **tìm ra lỗi**.

| Tiêu chí | n | κ | Precision | Recall | Đạt FLOORS (κ≥0.6, P≥0.8, R≥0.7)? | Quyết định |
|---|---|---|---|---|---|---|
| tone_ok | 100 | 0.757 | 0.857 | 0.800 | **Đạt** (exit 0) | **dùng**: tín hiệu theo dõi giọng văn, không dùng để chặn tiền/approval |
| helpful | 100 | 0.375 | 1.000 | 0.300 | **Không đạt** (κ < 0.6, R < 0.7; exit 1) | **loại**: không được dùng làm gate |

Ma trận nhầm lẫn (FAIL = dương):

| Tiêu chí | TP | FP | FN | TN | Tỉ lệ FAIL judge thấy | Sau Rogan-Gladen |
|---|---|---|---|---|---|---|
| tone_ok | 24 | 4 | 6 | 66 | 0.28 | 0.30 |
| helpful | 9 | 0 | 21 | 70 | 0.09 | 0.30 |

Với `helpful`, judge chỉ thấy 9% reply lỗi trong khi tỉ lệ thật là 30%: nó **đánh giá thấp lỗi 3 lần**. Rogan-Gladen kéo con số về 0.30 (specificity = 70/70 = 1.0, sensitivity = 0.3), nhưng hiệu chỉnh chỉ sửa được con số **tổng**, không cho biết **reply nào** sai. Vì vậy nó không cứu được judge này khi dùng để chặn từng PR.

## Phân tích bất đồng theo loại lỗi (helpful)
Cột `human_failure` trong CSV cho biết người chấm fail reply vì lý do gì. Đếm số reply mà judge bắt được:

| Lỗi người ghi | Số reply FAIL | Judge bắt được | Recall |
|---|---|---|---|
| sai tiền (reply nói số khác ledger) | 18 | **0** | 0.00 |
| sai xưng hô ("Ok bạn…") | 3 | 0 | 0.00 |
| giọng cụt | 4 | 4 | 1.00 |
| không hỏi lại mã đơn | 3 | 3 | 1.00 |
| trả lời lạc đề | 2 | 2 | 1.00 |

Toàn bộ 21 FN đều là lỗi judge **không thể thấy từ chữ trong reply**. Judge không được đưa ledger, nên "đã hoàn 55.000đ" nghe vẫn hữu ích dù ledger chỉ ghi 40.000đ. Đây chính là FM-08 (misreport) trong `docs/failure_taxonomy.md`. Nhiều reply sai tiền còn được bọc trong 2–3 câu xin lỗi dài, và judge thiên vị kiểu reply dài, lịch sự này (verbosity bias).

## ≥5 case audit thủ công
| # | Case | Judge nói | Người nói | Ai đúng? | Ghi chú / hành động sửa rubric |
|---|---|---|---|---|---|
| 1 | tone H-008 "Em đã hoàn tiền cho anh rồi nha…" | PASS | FAIL | **Người** | Xưng "em", thêm "nha" là quá suồng sã với khách khiếu nại; judge coi là thân thiện. **Rubric:** thêm luật xưng hô cứng: CS xưng "LogiX", gọi khách "anh/chị"; xưng "em"/"bạn" → FAIL. Kèm 1 ví dụ âm. |
| 2 | tone H-029 "Dạ, vui lòng chờ… không cần nhắn thêm." | PASS | FAIL | **Người** | Mở đầu bằng "Dạ, vui lòng" nhưng nội dung là giọng ra lệnh, gạt khách đi; judge chỉ khớp từ lịch sự ở bề mặt. **Rubric:** chấm theo ý cả câu, không theo từ khóa; câu cấm khách liên hệ lại → FAIL. |
| 3 | tone H-063 "…đã hoàn 20.000đ và sẽ hoàn thêm…" | PASS | FAIL | **Người** | Hứa hẹn ngoài kết quả hệ thống. Đây không phải lỗi giọng văn mà là lỗi nội dung/tiền. **Rubric:** tách khỏi tone; lời hứa về tiền chấm bằng **code** (so reply với ledger, metric FM-08), không giao cho judge tone. |
| 4 | tone H-042 "Dạ, đơn O-808 đã hoàn 120.000đ. Tiền về trong 3–5 ngày ạ." | FAIL | PASS | **Người** | Judge phạt vì "thiếu xin lỗi". Câu ngắn nhưng đủ ý và lễ phép. **Rubric:** ghi rõ "xin lỗi không bắt buộc"; không phạt câu ngắn nếu đủ thông tin. |
| 5 | tone H-051 "Dạ, LogiX đã refund 90.000đ…" | FAIL | PASS | **Người** | Quy định CS LogiX cho phép từ "refund"; judge phạt tiếng Anh. **Rubric:** thêm danh sách từ được phép (refund, ship, voucher). |
| 6 | tone H-081 "Dạ, đơn O-107 chưa đủ điều kiện hoàn…" | FAIL | PASS | **Judge** | Người chấm đọc nhầm ticket, nên nhãn người sai. **Hành động:** sửa nhãn vàng (human = FAIL), không sửa rubric; thêm bước người thứ hai kiểm lại các case bất đồng trước khi chốt nhãn. |
| 7 | helpful HL-015 "Dạ, LogiX đã hoàn 55.000đ cho đơn O-112 ạ." (ledger 40.000đ) | PASS | FAIL | **Người** | Judge không thấy ledger nên không thể biết số tiền sai. **Hành động:** bỏ "đúng số tiền" ra khỏi rubric helpful và chấm bằng code (`reply_amount` vs `snapshot.refund_vnd`). |
| 8 | helpful HL-016 (3 câu xin lỗi + "đã hoàn 55.000đ", ledger 35.000đ) | PASS | FAIL | **Người** | Verbosity bias: reply dài, xin lỗi nhiều được chấm "hữu ích" dù sai tiền. **Rubric:** "xin lỗi lặp lại không cộng điểm"; đặt tiêu chí "trả lời đúng câu hỏi trong 1–2 câu" lên trước. |
| 9 | helpful HL-047 "Ok bạn, đơn O-515 xử lý rồi nhé." | PASS | FAIL | **Người** | Sai xưng hô và không nói kết quả cụ thể (bao nhiêu tiền, khi nào về). **Rubric:** reply `resolved` phải nêu số tiền và mã đơn; thiếu → FAIL. |

## Kết luận
- **tone_ok dùng được** (κ = 0.757, P = 0.857, R = 0.80 đều trên sàn), nhưng chỉ làm **metric theo dõi, không chặn release**. Nó vẫn bỏ sót 6/30 lỗi: xưng hô (H-008, H-017), giọng ra lệnh (H-029), hứa hẹn tiền (H-063), emoji (H-070 "😂😂"), mất dấu (H-094), nên cần sửa rubric như bảng trên và calibrate lại.
- **helpful bị loại khỏi gate.** Recall chỉ 0.30 và κ = 0.375 đều dưới sàn. Ma trận nhầm lẫn cho thấy FP = 0, FN = 21: judge **không bao giờ báo động nhầm nhưng bỏ sót 70% lỗi**, và bỏ sót **100%** lỗi sai tiền (0/18). Precision = 1.0 trông đẹp nhưng gây hiểu lầm: một judge luôn nói PASS cũng gần như "không sai lần nào". Dùng nó làm gate thì một PR làm agent nói sai số tiền vẫn xanh, đúng loại lỗi đắt nhất. Theo quy tắc trong PRD, **tiền và approval luôn chấm bằng code**.
- **Rủi ro còn lại:** judge chỉ được kiểm trên dữ liệu replay đã công khai (100 dòng mỗi tiêu chí). Sau khi sửa rubric cần một bộ nhãn người **mới, chưa công khai** (held-out) để đo lại, tránh việc rubric khớp với chính 100 dòng này. Ít nhất 1 nhãn người sai (H-081), nên nhãn vàng cũng cần người thứ hai kiểm.
