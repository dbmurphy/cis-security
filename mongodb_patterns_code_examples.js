// MongoDB Lookup Patterns - Code Examples
// =====================================

// Sample Data Structure
// Collection A: orders (500,000 documents)
// Collection B: products (5 documents)

/* 
Collection A (orders):
{
  _id: ObjectId("..."),
  orderId: "ORD-001",
  productId: ObjectId("prod1"),  // Reference to Collection B
  quantity: 2,
  orderDate: ISODate("2024-01-01"),
  customerId: "CUST-123"
}

Collection B (products):
{
  _id: ObjectId("prod1"),
  name: "Laptop",
  price: 999.99,
  category: "Electronics"
}
*/

// ============================================================================
// PATTERN 1: $lookup Aggregation (POOR PERFORMANCE)
// ============================================================================

console.log("PATTERN 1: Using $lookup aggregation");
console.log("=====================================");

const pattern1_lookup = () => {
  const startTime = Date.now();
  
  // This performs poorly with large source collections
  const result = db.orders.aggregate([
    {
      $lookup: {
        from: "products",
        localField: "productId",
        foreignField: "_id",
        as: "productDetails"
      }
    },
    {
      $unwind: "$productDetails"  // Optional: flatten the array
    },
    {
      $project: {
        orderId: 1,
        quantity: 1,
        orderDate: 1,
        customerId: 1,
        productName: "$productDetails.name",
        productPrice: "$productDetails.price",
        totalValue: { $multiply: ["$quantity", "$productDetails.price"] }
      }
    }
  ]).toArray();
  
  const endTime = Date.now();
  
  console.log(`Pattern 1 Results: ${result.length} documents`);
  console.log(`Execution time: ${endTime - startTime}ms`);
  console.log("Performance Issues:");
  console.log("- MongoDB processes ALL 500,000 orders");
  console.log("- Performs 500,000 individual lookups to products collection");
  console.log("- High memory usage for result set");
  console.log("- Large network transfer (500,000 enriched documents)");
  
  return result;
};

// ============================================================================
// PATTERN 2: Aggregation + Driver-Side Resolution (GOOD PERFORMANCE)
// ============================================================================

console.log("\nPATTERN 2: Aggregation + Driver-side resolution");
console.log("===============================================");

const pattern2_optimized = async () => {
  const startTime = Date.now();
  
  // STEP 1: Aggregate orders by productId (group similar orders)
  console.log("Step 1: Grouping orders by productId...");
  const groupedOrders = await db.orders.aggregate([
    {
      $group: {
        _id: "$productId",  // Group by product reference
        orders: { $push: "$$ROOT" },  // Keep all order documents
        totalQuantity: { $sum: "$quantity" },
        orderCount: { $sum: 1 }
      }
    }
  ]).toArray();
  
  console.log(`Grouped into ${groupedOrders.length} product groups`);
  
  // STEP 2: Extract unique product IDs
  const productIds = groupedOrders.map(group => group._id);
  console.log(`Unique product IDs: ${productIds.length}`);
  
  // STEP 3: Single lookup to products collection (only 5 documents!)
  console.log("Step 2: Fetching product details...");
  const products = await db.products.find({
    _id: { $in: productIds }
  }).toArray();
  
  // Create a map for quick product lookup
  const productMap = {};
  products.forEach(product => {
    productMap[product._id.toString()] = product;
  });
  
  // STEP 4: Merge results in application code
  console.log("Step 3: Merging results...");
  const enrichedResults = [];
  
  groupedOrders.forEach(group => {
    const product = productMap[group._id.toString()];
    
    // Process each order in the group
    group.orders.forEach(order => {
      enrichedResults.push({
        orderId: order.orderId,
        quantity: order.quantity,
        orderDate: order.orderDate,
        customerId: order.customerId,
        productName: product.name,
        productPrice: product.price,
        totalValue: order.quantity * product.price
      });
    });
  });
  
  const endTime = Date.now();
  
  console.log(`Pattern 2 Results: ${enrichedResults.length} documents`);
  console.log(`Execution time: ${endTime - startTime}ms`);
  console.log("Performance Benefits:");
  console.log("- MongoDB groups 500,000 orders efficiently");
  console.log("- Only 1 lookup query to products collection");
  console.log("- Fetches only 5 product documents");
  console.log("- Low memory usage during aggregation");
  console.log("- Minimal network transfer");
  
  return enrichedResults;
};

// ============================================================================
// ALTERNATIVE PATTERN 2 IMPLEMENTATION: More Memory Efficient
// ============================================================================

const pattern2_memory_efficient = async () => {
  console.log("\nPATTERN 2 (Memory Efficient): Processing in batches");
  console.log("===================================================");
  
  const startTime = Date.now();
  
  // STEP 1: Get distinct product IDs without loading all orders
  const distinctProducts = await db.orders.distinct("productId");
  console.log(`Found ${distinctProducts.length} distinct products`);
  
  // STEP 2: Fetch all product details
  const products = await db.products.find({
    _id: { $in: distinctProducts }
  }).toArray();
  
  const productMap = {};
  products.forEach(product => {
    productMap[product._id.toString()] = product;
  });
  
  // STEP 3: Process orders in batches with cursor
  const batchSize = 10000;
  let processedCount = 0;
  const enrichedResults = [];
  
  const cursor = db.orders.find({}).batchSize(batchSize);
  
  while (await cursor.hasNext()) {
    const order = await cursor.next();
    const product = productMap[order.productId.toString()];
    
    if (product) {
      enrichedResults.push({
        orderId: order.orderId,
        quantity: order.quantity,
        orderDate: order.orderDate,
        customerId: order.customerId,
        productName: product.name,
        productPrice: product.price,
        totalValue: order.quantity * product.price
      });
    }
    
    processedCount++;
    if (processedCount % 50000 === 0) {
      console.log(`Processed ${processedCount} orders...`);
    }
  }
  
  const endTime = Date.now();
  
  console.log(`Pattern 2 (Efficient) Results: ${enrichedResults.length} documents`);
  console.log(`Execution time: ${endTime - startTime}ms`);
  console.log("Additional Benefits:");
  console.log("- Constant memory usage regardless of collection size");
  console.log("- Can process collections larger than available RAM");
  console.log("- Suitable for real-time streaming scenarios");
  
  return enrichedResults;
};

// ============================================================================
// PERFORMANCE COMPARISON RUNNER
// ============================================================================

const runPerformanceComparison = async () => {
  console.log("MongoDB Lookup Patterns Performance Comparison");
  console.log("==============================================\n");
  
  // Note: In a real scenario, you would uncomment these based on your data size
  
  // For small datasets (< 10,000 docs), Pattern 1 might be acceptable
  // const results1 = pattern1_lookup();
  
  // For large datasets (> 100,000 docs), always use Pattern 2
  const results2 = await pattern2_optimized();
  
  // For very large datasets (> 1,000,000 docs), use memory-efficient version
  // const results3 = await pattern2_memory_efficient();
  
  console.log("\n=== SUMMARY ===");
  console.log("Pattern 1 ($lookup): Simple code, poor performance with large datasets");
  console.log("Pattern 2 (Optimized): Complex code, excellent performance");
  console.log("Pattern 2 (Memory Efficient): Most complex, handles any dataset size");
};

// ============================================================================
// INDEX RECOMMENDATIONS
// ============================================================================

console.log("\nRECOMMENDED INDEXES:");
console.log("===================");

// Essential indexes for both patterns
const createIndexes = () => {
  // Index on the reference field in Collection A
  db.orders.createIndex({ "productId": 1 });
  
  // Compound index for common queries
  db.orders.createIndex({ "productId": 1, "orderDate": -1 });
  
  // Index on the primary key of Collection B (usually already exists)
  db.products.createIndex({ "_id": 1 });
  
  console.log("Created essential indexes for optimal performance");
};

// ============================================================================
// WHEN TO USE EACH PATTERN
// ============================================================================

console.log("\nDECISION MATRIX:");
console.log("================");
console.log("Use Pattern 1 ($lookup) when:");
console.log("- Source collection < 10,000 documents");
console.log("- Simple queries with minimal processing");
console.log("- Development speed is more important than performance");
console.log("- One-off analytical queries");

console.log("\nUse Pattern 2 (Optimized) when:");
console.log("- Source collection > 100,000 documents");
console.log("- Reference collection is small (< 1,000 docs)");
console.log("- High-frequency queries");
console.log("- Performance is critical");
console.log("- Memory usage needs to be controlled");

// Export for use in applications
module.exports = {
  pattern1_lookup,
  pattern2_optimized,
  pattern2_memory_efficient,
  runPerformanceComparison,
  createIndexes
};