#lang racket
;; Prototype 3 - FUNCTIONAL paradigm (Racket).
;; Same problem: answer, send to a vendor, or escalate.
;; Functional style: immutable structs, pure functions, recursion,
;; and higher-order functions (map, foldl, ormap). No variable is ever changed.

(provide (struct-out rule) (struct-out decision)
         default-rules triage triage-all count-routes)

(struct rule (words route urgency detail) #:transparent)
(struct decision (route urgency detail) #:transparent)

(define default-rules
  (list
   (rule '("gas" "smoke" "fire" "spark" "carbon monoxide") 'escalate 10 "safety keyword")
   (rule '("locked out" "lockout" "lost my key") 'escalate 8 "lockout")
   (rule '("trash" "garbage" "recycling") 'answer 1 "Trash and recycling go out Tuesday night.")
   (rule '("quiet hours" "noise") 'answer 1 "Quiet hours are 10 pm to 7 am.")
   (rule '("leak" "clog" "toilet" "drain") 'vendor 5 "Liberty Plumbing")
   (rule '("light" "outlet" "switch" "breaker") 'vendor 5 "Brightside Electric")))

;; Does the message mention any word of this rule?
(define (rule-matches? r text)
  (ormap (lambda (word) (string-contains? text word)) (rule-words r)))

;; Recursion: walk the rule list until one matches. Returns a rule or #f.
(define (first-match rules text)
  (cond [(empty? rules) #f]
        [(rule-matches? (first rules) text) (first rules)]
        [else (first-match (rest rules) text)]))

;; Pure function: same input always gives the same decision.
(define (triage rules message)
  (define matched (first-match rules (string-downcase message)))
  (if matched
      (decision (rule-route matched) (rule-urgency matched) (rule-detail matched))
      (decision 'escalate 5 "no rule matched - landlord decides")))

(define (triage-all rules messages)
  (map (lambda (m) (triage rules m)) messages))

;; foldl builds a NEW hash each step instead of changing a counter.
(define (count-routes decisions)
  (foldl (lambda (d counts) (hash-update counts (decision-route d) add1 0))
         (hash)
         decisions))
