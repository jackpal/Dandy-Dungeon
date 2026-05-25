(defproject dandy-clojurescript "0.0.1"
  :description "Dandy in clojurescript"
  :source-paths ["src-clj"]
  :dependencies [[org.clojure/clojure "1.5.1"]]
  :plugins [[lein-cljsbuild "0.3.2"]]
  :jvm-opts ["--add-opens=java.base/jdk.internal.loader=ALL-UNNAMED"
             "--add-opens=java.base/java.lang=ALL-UNNAMED"]
  :cljsbuild {
    :builds [{:source-paths ["src-cljs"]
              :compiler {:output-to "resources/public/js/main.js"
                         :optimizations :whitespace
                         :pretty-print true}}]}
)
